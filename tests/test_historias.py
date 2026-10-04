import random
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardianes.hu01_asignar_cuadrilla import AsignacionRechazada, Cuadrilla, Despacho
from guardianes.hu02_coordenadas import CoordenadasFueraDeLimite, calcular_ruta, calcular_ruta_cronometrada, crear_punto
from guardianes.hu03_panel import Jornada, PanelControl
from guardianes.hu04_ahorro import estimar_ahorro
from guardianes.hu05_omitir_punto import PuntoFijo, omitir_por_clima
from guardianes.hu06_embarcacion import ESTANDAR, Catalogo, consumo_ruta
from guardianes.hu07_registro_kg import FormatoInvalido, RegistroJornada, parsear_kg
from guardianes.hu08_validacion import ErrorValidacion, validar_coordenada_texto, validar_entrada
from guardianes.hu09_alerta_combustible import AMARILLO, ROJO, VERDE, evaluar_combustible
from guardianes.hu10_tipo_residuo import desglose_porcentual, filtrar_historial, validar_residuo
from guardianes.hu11_historial import VACIO, Historial
from guardianes.hu12_exportar import ErrorExportacion, exportar_txt, generar_resumen
from guardianes.hu13_auditoria import Auditoria
from guardianes.hu14_muelles import Muelles
from guardianes.nucleo import COMPLETADO, OMITIDO, Embarcacion, Punto, Ruta, longitud_ruta

BASE = Punto("Base", 10.96, -74.80)
A, B, C, D = (Punto("A", 10.99, -74.85), Punto("B", 10.93, -74.78),
              Punto("C", 11.02, -74.79), Punto("D", 10.95, -74.88))
LANCHA = Embarcacion("Lancha", "M1", 1.0, 100.0)


def ruta_demo():
    return Ruta("R-1", BASE, [Punto(p.nombre, p.lat, p.lon) for p in (A, B, C)])


class TestHU01(unittest.TestCase):
    def test_criterios(self):
        d = Despacho([Cuadrilla("Alfa"), Cuadrilla("Beta")])
        self.assertEqual(len(d.disponibles()), 2)
        d.asignar(ruta_demo(), "Alfa")
        self.assertEqual(d.panel_general()["Alfa"], "En Operación")
        with self.assertRaises(AsignacionRechazada):
            d.asignar(ruta_demo(), "Alfa")


class TestHU02(unittest.TestCase):
    def test_ruta_valida(self):
        ruta = calcular_ruta(BASE, [A, B, C])
        self.assertEqual(len(ruta.puntos), 3)

    def test_fuera_de_limite(self):
        with self.assertRaisesRegex(CoordenadasFueraDeLimite, "Coordenadas fuera de límite"):
            crear_punto("X", 40.0, -3.7)

    def test_50_puntos_en_2_segundos(self):
        random.seed(1)
        pts = [Punto(f"P{i}", random.uniform(10.85, 11.1), random.uniform(-74.95, -74.7)) for i in range(50)]
        _, seg = calcular_ruta_cronometrada(BASE, pts)
        self.assertLess(seg, 2.0)


class TestHU03(unittest.TestCase):
    def setUp(self):
        self.panel = PanelControl()
        self.panel.registrar(Jornada(date(2026, 9, 5), 80, 100, 30))

    def test_mes_con_datos_y_grafico(self):
        r = self.panel.resumen_mes(2026, 9)
        self.assertEqual(r["combustible_ahorrado_l"], 20)
        self.assertIn("Sin optimizador", self.panel.grafico_barras(2026, 9))

    def test_mes_vacio_en_cero(self):
        r = self.panel.resumen_mes(2026, 1)
        self.assertTrue(all(v == 0 for v in r.values()))
        self.panel.grafico_barras(2026, 1)

    def test_pdf(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = self.panel.generar_pdf(2026, 9, Path(t) / "panel.pdf")
            datos = ruta.read_bytes()
        self.assertTrue(datos.startswith(b"%PDF-1.4"))
        self.assertTrue(datos.rstrip().endswith(b"%%EOF"))


class TestHU04(unittest.TestCase):
    def test_ahorro_y_meta(self):
        ingreso = [A, B, C, D]
        a = estimar_ahorro(BASE, ingreso, LANCHA)
        self.assertGreaterEqual(a.porcentaje, 0)
        self.assertIn("litros", a.reporte())

    def test_ruta_igual_es_optima(self):
        optima = calcular_ruta(BASE, [A, B, C]).puntos
        a = estimar_ahorro(BASE, optima, LANCHA, optima)
        self.assertEqual(a.porcentaje, 0.0)
        self.assertIn("0%", a.reporte())
        self.assertIn("óptima", a.reporte())


class TestHU05(unittest.TestCase):
    def test_omitir_intermedio(self):
        ruta = ruta_demo()
        nueva = omitir_por_clima(ruta, "B")
        self.assertEqual([p.estado for p in nueva.puntos].count(OMITIDO), 1)
        self.assertAlmostEqual(nueva.distancia_km, longitud_ruta(BASE, [ruta.puntos[0], ruta.puntos[2]]))
        self.assertIn("[Omitido]", "\n".join(nueva.detalle()))
        self.assertNotEqual(ruta.puntos[1].estado, OMITIDO)

    def test_puntos_fijos(self):
        ruta = ruta_demo()
        with self.assertRaises(PuntoFijo):
            omitir_por_clima(ruta, "Base")
        with self.assertRaises(PuntoFijo):
            omitir_por_clima(ruta, "C")


class TestHU06(unittest.TestCase):
    def test_consumo_y_defecto(self):
        cat = Catalogo()
        e, aviso = cat.seleccionar("Lancha Rápida")
        self.assertIsNone(aviso)
        self.assertEqual(consumo_ruta(10, e), 10 * e.consumo_l_km)
        e, aviso = cat.seleccionar(None)
        self.assertEqual(e.nombre, ESTANDAR)
        self.assertTrue(aviso)

    def test_nueva_lancha_persiste(self):
        with tempfile.TemporaryDirectory() as t:
            archivo = Path(t) / "lanchas.json"
            Catalogo(archivo).agregar("Delfín", "D-30", 1.7, 90)
            self.assertIn("Delfín", Catalogo(archivo).items)


class TestHU07(unittest.TestCase):
    def test_formato_y_obligatorio(self):
        for malo in ("-5", "abc"):
            with self.assertRaisesRegex(FormatoInvalido, "Formato inválido"):
                parsear_kg(malo)
        with self.assertRaises(ValueError):
            parsear_kg("")

    def test_total_de_la_jornada(self):
        j = RegistroJornada(omitir_por_clima(ruta_demo(), "B"))
        j.completar_punto("A", "10.5", "Plásticos")
        with self.assertRaises(ValueError):
            j.cerrar_jornada()
        j.completar_punto("C", 4, "Metales/Vidrios")
        self.assertEqual(j.cerrar_jornada(), 14.5)


class TestHU08(unittest.TestCase):
    def test_errores_especificos(self):
        r = validar_entrada(BASE, [A, Punto("A", 10.0, -74.8), Punto("", 10.9, -74.8)])
        txt = " ".join(r.errores)
        self.assertFalse(r.puede_calcular)
        for esperado in ("Duplicado", "Fuera de rango", "Dato vacío"):
            self.assertIn(esperado, txt)

    def test_sintaxis_y_exito(self):
        with self.assertRaises(ErrorValidacion):
            validar_coordenada_texto("10.9a")
        self.assertEqual(validar_coordenada_texto("-74.8"), -74.8)
        self.assertTrue(validar_entrada(BASE, [A, B]).puede_calcular)


class TestHU09(unittest.TestCase):
    def test_colores(self):
        rojo = evaluar_combustible(LANCHA, 120)
        self.assertEqual(rojo.color, ROJO)
        self.assertIn("Combustible Insuficiente", rojo.mensaje)
        self.assertIn("dos días", rojo.sugerencia)
        amarillo = evaluar_combustible(LANCHA, 90)
        self.assertEqual((amarillo.color, amarillo.mensaje), (AMARILLO, "Nivel de combustible al límite"))
        self.assertEqual(evaluar_combustible(LANCHA, 50).color, VERDE)


def ruta_con_residuos():
    r = ruta_demo()
    j = RegistroJornada(r)
    j.completar_punto("A", 30, "Plásticos")
    j.completar_punto("B", 10, "Maderas/Orgánicos")
    j.completar_punto("C", 10, "Plásticos")
    j.cerrar_jornada()
    return r


class TestHU10(unittest.TestCase):
    def test_menu_obligatorio(self):
        with self.assertRaises(ValueError):
            validar_residuo(None)
        with self.assertRaises(ValueError):
            validar_residuo("Papel")

    def test_filtro_y_desglose(self):
        h = Historial()
        h.guardar(ruta_con_residuos())
        res = filtrar_historial(h.registros, "Plásticos")
        self.assertEqual(len(res[0][1]), 2)
        self.assertEqual(filtrar_historial(h.registros, "Metales/Vidrios"), [])
        d = desglose_porcentual(h.registros[0].puntos)
        self.assertEqual(d["Plásticos"], 80.0)
        self.assertEqual(d["Maderas/Orgánicos"], 20.0)


class TestHU11(unittest.TestCase):
    def test_vacio_listado_y_filtros(self):
        h = Historial()
        self.assertEqual(h.listar(), VACIO)
        h.guardar(ruta_demo(), datetime(2026, 9, 7, 8))
        h.guardar(ruta_demo(), datetime(2026, 8, 20, 8))
        self.assertIn("R-1", h.listar())
        self.assertEqual(len(h.por_mes(2026, 9)), 1)
        self.assertEqual(len(h.por_semana(date(2026, 9, 10))), 1)

    def test_json(self):
        h = Historial()
        h.guardar(ruta_demo(), datetime(2026, 9, 7, 8))
        with tempfile.TemporaryDirectory() as t:
            h.guardar_json(Path(t) / "h.json")
            self.assertEqual(len(Historial.cargar_json(Path(t) / "h.json").registros), 1)


class TestHU12(unittest.TestCase):
    def test_encabezado_y_archivo(self):
        txt = generar_resumen(ruta_con_residuos(), LANCHA, datetime(2026, 9, 7, 8, 30))
        for esperado in ("Fecha: 2026-09-07", "Hora de generación: 08:30:00", "Lancha asignada: Lancha",
                         "Distancia total", "Plásticos: 80.0%"):
            self.assertIn(esperado, txt)
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(exportar_txt(ruta_demo(), LANCHA, t).exists())

    def test_error_de_permisos(self):
        with mock.patch.object(Path, "write_text", side_effect=PermissionError):
            with self.assertRaisesRegex(ErrorExportacion, "carpeta de destino"):
                exportar_txt(ruta_demo(), LANCHA, ".")


class TestHU13(unittest.TestCase):
    def test_registro_tabla_y_solo_lectura(self):
        a = Auditoria()
        a.registrar("capitan1", "Omitir B", ["A", "B", "C"], ["A", "C"])
        self.assertEqual(len(a.buscar_por_fecha(date.today())), 1)
        tabla = a.tabla_comparativa(date.today())
        self.assertIn("A > B > C", tabla)
        self.assertIn("A > C", tabla)
        with self.assertRaises(PermissionError):
            a.eliminar(0)
        with self.assertRaises(PermissionError):
            a.modificar(0)


class TestHU14(unittest.TestCase):
    def test_sugerencia_forzar_y_limites(self):
        m = Muelles()
        m.registrar("Muelle Norte", 11.05, -74.82)
        m.registrar("Muelle Sur", 10.90, -74.80)
        m.registrar("Muelle Centro", 10.97, -74.80)
        plan = m.planificar([A, B, C])
        self.assertEqual(plan.sugerido, min(plan.distancias_km, key=plan.distancias_km.get))
        plan.forzar("Muelle Sur")
        self.assertEqual(plan.elegido, "Muelle Sur")
        with self.assertRaisesRegex(ValueError, "Ubicación fuera de rango"):
            m.registrar("Lejano", 20.0, -60.0)


if __name__ == "__main__":
    unittest.main()
