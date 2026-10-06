"""Un escenario ejecutable por cada criterio de aceptación (HU-01 a HU-14).

No depende de ninguna interfaz: cada función recibe un Contexto y devuelve
(cumple, texto). La ventana (simulador.py) solo muestra estos resultados.
"""
from __future__ import annotations

import random
import tempfile
import time
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Callable
from unittest import mock

from .hu01_asignar_cuadrilla import AsignacionRechazada, Cuadrilla, Despacho
from .hu02_coordenadas import CoordenadasFueraDeLimite, calcular_ruta, crear_punto
from .hu03_panel import Jornada, PanelControl
from .hu04_ahorro import estimar_ahorro
from .hu05_omitir_punto import PuntoFijo, omitir_por_clima
from .hu06_embarcacion import ESTANDAR, Catalogo, consumo_ruta
from .hu07_registro_kg import FormatoInvalido, RegistroJornada
from .hu08_validacion import ErrorValidacion, validar_coordenada_texto, validar_entrada
from .hu09_alerta_combustible import AMARILLO, ROJO, evaluar_combustible
from .hu10_tipo_residuo import desglose_porcentual, filtrar_historial, validar_residuo
from .hu11_historial import VACIO, Historial
from .hu12_exportar import ErrorExportacion, exportar_txt, generar_resumen
from .hu13_auditoria import Auditoria
from .hu14_muelles import Muelles
from .nucleo import TIPOS_RESIDUO, Embarcacion, Punto

SALIDAS = Path("salidas")
Resultado = tuple[bool, str]


@dataclass
class Contexto:
    base: Punto
    puntos: list[Punto]

    @classmethod
    def por_defecto(cls) -> "Contexto":
        return cls(
            Punto("Muelle Centro", 10.96, -74.80),
            [Punto("Dársena 1", 10.99, -74.85), Punto("Desembocadura", 10.93, -74.78),
             Punto("Canal Norte", 11.02, -74.79), Punto("Muelle viejo", 10.95, -74.88)])

    def copia(self) -> list[Punto]:
        return [replace(p) for p in self.puntos]

    def ruta(self):
        return calcular_ruta(self.base, self.copia())


def _lancha() -> Embarcacion:
    return Catalogo().seleccionar(None)[0]


def _ruta_completada(ctx: Contexto):
    ruta = ctx.ruta()
    jornada = RegistroJornada(ruta)
    for i, p in enumerate(ruta.puntos):
        jornada.completar_punto(p.nombre, 10 * (i + 1), TIPOS_RESIDUO[i % 3])
    jornada.cerrar_jornada()
    return ruta


# ---------------------------------------------------------------- HU-01
def _hu01_c1(ctx: Contexto) -> Resultado:
    d = Despacho([Cuadrilla("Alfa"), Cuadrilla("Beta")])
    nombres = [c.nombre for c in d.disponibles()]
    return nombres == ["Alfa", "Beta"], "Equipos operativos disponibles: " + ", ".join(nombres)


def _hu01_c2(ctx: Contexto) -> Resultado:
    d = Despacho([Cuadrilla("Alfa"), Cuadrilla("Beta")])
    antes = d.panel_general()["Alfa"]
    d.asignar(ctx.ruta(), "Alfa")
    despues = d.panel_general()["Alfa"]
    return (antes == "Disponible" and despues == "En Operación",
            f"Ruta asignada a la Cuadrilla Alfa.\nPanel general: Alfa pasó de «{antes}» a «{despues}»")


def _hu01_c3(ctx: Contexto) -> Resultado:
    d = Despacho([Cuadrilla("Alfa"), Cuadrilla("Beta")])
    ruta = ctx.ruta()
    d.asignar(ruta, "Alfa")
    try:
        d.asignar(ruta, "Alfa")
    except AsignacionRechazada as e:
        return True, f"Asignación rechazada.\n{e}"
    return False, "El sistema aceptó asignar una cuadrilla que ya estaba En Operación"


# ---------------------------------------------------------------- HU-02
def _hu02_c1(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    texto = "\n".join(ruta.detalle()) + f"\nDistancia total: {ruta.distancia_km:.2f} km"
    return len(ruta.puntos) == len(ctx.puntos), "Ruta óptima generada:\n" + texto


def _hu02_c2(ctx: Contexto) -> Resultado:
    try:
        crear_punto("Fuera del área", 40.0, -3.7)
    except CoordenadasFueraDeLimite as e:
        return True, f"Acción bloqueada con el mensaje: «{e}»"
    return False, "El sistema aceptó coordenadas fuera del área navegable"


def _hu02_c3(ctx: Contexto) -> Resultado:
    random.seed(7)
    pts = [Punto(f"P{i}", random.uniform(10.85, 11.1), random.uniform(-74.95, -74.7)) for i in range(50)]
    t0 = time.perf_counter()
    calcular_ruta(ctx.base, pts)
    seg = time.perf_counter() - t0
    return seg < 2.0, f"Ruta con 50 puntos calculada en {seg:.3f} s (máximo permitido: 2 s)"


# ---------------------------------------------------------------- HU-03
def _panel() -> PanelControl:
    p = PanelControl()
    p.registrar(Jornada(date(2026, 9, 5), 80, 100, 30))
    p.registrar(Jornada(date(2026, 9, 19), 60, 75, 22))
    return p


def _hu03_c1(ctx: Contexto) -> Resultado:
    g = _panel().grafico_barras(2026, 9)
    return "Sin optimizador" in g, g


def _hu03_c2(ctx: Contexto) -> Resultado:
    p = _panel()
    r = p.resumen_mes(2026, 1)
    return all(v == 0 for v in r.values()), f"Enero 2026 (sin jornadas): {r}\n\n{p.grafico_barras(2026, 1)}"


def _hu03_c3(ctx: Contexto) -> Resultado:
    SALIDAS.mkdir(exist_ok=True)
    destino = _panel().generar_pdf(2026, 9, SALIDAS / "panel_septiembre_2026.pdf")
    ok = destino.exists() and destino.read_bytes().startswith(b"%PDF")
    return ok, f"PDF generado: {destino.resolve()}"


# ---------------------------------------------------------------- HU-04
def _hu04_c1(ctx: Contexto) -> Resultado:
    a = estimar_ahorro(ctx.base, ctx.copia(), _lancha())
    return a.porcentaje >= 0, (f"Recorrido empírico (orden de ingreso): {a.km_empirico:.2f} km\n"
                               f"Ruta calculada: {a.km_calculado:.2f} km\n{a.reporte()}")


def _hu04_c2(ctx: Contexto) -> Resultado:
    optima = ctx.ruta().puntos
    a = estimar_ahorro(ctx.base, optima, _lancha(), optima)
    return a.porcentaje == 0.0 and "óptima" in a.reporte(), "Trayecto empírico igual al calculado:\n" + a.reporte()


def _hu04_c3(ctx: Contexto) -> Resultado:
    rep = estimar_ahorro(ctx.base, ctx.copia(), _lancha()).reporte()
    return "litros" in rep, rep


# ---------------------------------------------------------------- HU-05
def _hu05_c1(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    if len(ruta.puntos) < 3:
        return False, "Se necesitan al menos 3 puntos para omitir uno intermedio"
    nombre = ruta.puntos[1].nombre
    nueva = omitir_por_clima(ruta, nombre)
    ok = nueva.distancia_km <= ruta.distancia_km + 1e-9
    return ok, (f"Omitido por clima: {nombre}\nDistancia antes: {ruta.distancia_km:.2f} km\n"
                f"Distancia recalculada: {nueva.distancia_km:.2f} km (une el nodo anterior con el siguiente)")


def _hu05_c2(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    nueva = omitir_por_clima(ruta, ruta.puntos[1].nombre)
    detalle = "\n".join(nueva.detalle())
    return "[Omitido]" in detalle, "Historial de la ruta:\n" + detalle


def _hu05_c3(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    mensajes = []
    for nombre in (ruta.base.nombre, ruta.puntos[-1].nombre):
        try:
            omitir_por_clima(ruta, nombre)
            return False, f"El sistema dejó omitir {nombre}"
        except PuntoFijo as e:
            mensajes.append(f"{nombre}: bloqueado. {e}")
    return True, "\n".join(mensajes)


# ---------------------------------------------------------------- HU-06
def _hu06_c1(ctx: Contexto) -> Resultado:
    e = Catalogo().seleccionar("Lancha Rápida")[0]
    dist = ctx.ruta().distancia_km
    consumo = consumo_ruta(dist, e)
    return (abs(consumo - dist * e.consumo_l_km) < 1e-9,
            f"{e.nombre}: factor {e.consumo_l_km} L/km\n{dist:.2f} km × {e.consumo_l_km} = {consumo:.2f} L")


def _hu06_c2(ctx: Contexto) -> Resultado:
    e, aviso = Catalogo().seleccionar(None)
    return e.nombre == ESTANDAR and bool(aviso), f"Embarcación usada: {e.nombre}\nAviso al usuario: {aviso}"


def _hu06_c3(ctx: Contexto) -> Resultado:
    with tempfile.TemporaryDirectory() as t:
        archivo = Path(t) / "lanchas.json"
        Catalogo(archivo).agregar("Delfín", "D-30", 1.7, 90)
        ok = "Delfín" in Catalogo(archivo).items
    return ok, "Lancha «Delfín» (modelo D-30, 1.7 L/km) guardada y encontrada al reabrir el catálogo"


# ---------------------------------------------------------------- HU-07
def _hu07_c1(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    j = RegistroJornada(ruta)
    nombre = ruta.puntos[0].nombre
    try:
        j.completar_punto(nombre, None, "Plásticos")
    except ValueError as e:
        j.completar_punto(nombre, 12.5, "Plásticos")
        return True, f"Sin peso: {e}\nCon 12.5 kg: {nombre} queda «{ruta.puntos[0].estado}»"
    return False, "El sistema dejó completar el punto sin peso"


def _hu07_c2(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    j = RegistroJornada(ruta)
    salidas = []
    for malo in ("-5", "abc"):
        try:
            j.completar_punto(ruta.puntos[0].nombre, malo, "Plásticos")
            return False, f"El sistema aceptó «{malo}»"
        except FormatoInvalido as e:
            salidas.append(f"«{malo}» → {e}")
    return True, "\n".join(salidas)


def _hu07_c3(ctx: Contexto) -> Resultado:
    ruta = ctx.ruta()
    j = RegistroJornada(ruta)
    for p in ruta.puntos:
        j.completar_punto(p.nombre, 10.0, "Plásticos")
    total = j.cerrar_jornada()
    return total == 10.0 * len(ruta.puntos), f"Jornada cerrada. Total recolectado: {total} kg"


# ---------------------------------------------------------------- HU-08
def _hu08_c1(ctx: Contexto) -> Resultado:
    malos = [Punto("A", 10.99, -74.85), Punto("A", 10.0, -74.8), Punto("", 10.95, -74.88)]
    r = validar_entrada(ctx.base, malos)
    return (not r.puede_calcular and bool(r.errores),
            "Datos con fallas:\n- " + "\n- ".join(r.errores) + "\nEl cálculo NO se ejecutó.")


def _hu08_c2(ctx: Contexto) -> Resultado:
    try:
        validar_coordenada_texto("10.9a$", "latitud")
    except ErrorValidacion as e:
        return True, f"Campo bloqueado: {e}"
    return False, "El sistema aceptó letras y símbolos en la coordenada"


def _hu08_c3(ctx: Contexto) -> Resultado:
    r = validar_entrada(ctx.base, ctx.copia())
    return (r.puede_calcular and not r.errores,
            "Todos los campos correctos: botón de cálculo habilitado, sin advertencias."
            if r.puede_calcular else "Errores:\n- " + "\n- ".join(r.errores))


# ---------------------------------------------------------------- HU-09
def _alerta(ctx: Contexto, factor: float):
    dist = ctx.ruta().distancia_km
    lancha = Embarcacion("Lancha de prueba", "P", 1.0, dist / factor)
    return evaluar_combustible(lancha, dist), dist, lancha


def _hu09_c1(ctx: Contexto) -> Resultado:
    a, dist, lancha = _alerta(ctx, 1.25)
    return (a.color == ROJO and "Combustible Insuficiente" in a.mensaje,
            f"Ruta de {dist:.1f} km con tanque de {lancha.tanque_l:.1f} L ({a.porcentaje_tanque:.0f}% del tanque)\n"
            f"BANNER ROJO: {a.mensaje}")


def _hu09_c2(ctx: Contexto) -> Resultado:
    a, _, _ = _alerta(ctx, 1.25)
    ok = bool(a.sugerencia) and "dos días" in a.sugerencia and "mayor capacidad" in a.sugerencia
    return ok, f"Sugerencia: {a.sugerencia}"


def _hu09_c3(ctx: Contexto) -> Resultado:
    a, _, _ = _alerta(ctx, 0.92)
    return (a.color == AMARILLO and a.mensaje == "Nivel de combustible al límite",
            f"Consumo al {a.porcentaje_tanque:.0f}% del tanque\nALERTA AMARILLA: {a.mensaje}")


# ---------------------------------------------------------------- HU-10
def _hu10_c1(ctx: Contexto) -> Resultado:
    try:
        validar_residuo(None)
    except ValueError as e:
        return True, f"Sin seleccionar tipo: {e}\nOpciones del menú: " + ", ".join(TIPOS_RESIDUO)
    return False, "El sistema dejó continuar sin tipo de residuo"


def _hu10_c2(ctx: Contexto) -> Resultado:
    h = Historial()
    h.guardar(_ruta_completada(ctx))
    res = filtrar_historial(h.registros, "Plásticos")
    lineas = [f"Ruta {r.ruta_id}: " + ", ".join(p.nombre for p in nodos) for r, nodos in res]
    return len(res) >= 1, "Filtro «Plásticos»:\n" + "\n".join(lineas)


def _hu10_c3(ctx: Contexto) -> Resultado:
    d = desglose_porcentual(_ruta_completada(ctx).puntos)
    return (abs(sum(d.values()) - 100) < 0.5,
            "Porcentaje del peso total por material:\n" + "\n".join(f"- {t}: {p}%" for t, p in d.items()))


# ---------------------------------------------------------------- HU-11
def _hu11_c1(ctx: Contexto) -> Resultado:
    h = Historial()
    h.guardar(ctx.ruta(), datetime(2026, 9, 7, 8, 0))
    h.guardar(ctx.ruta(), datetime(2026, 9, 14, 9, 30))
    texto = h.listar()
    return len(texto.splitlines()) == 2, "Fecha | Ruta | Distancia | Puntos\n" + texto


def _hu11_c2(ctx: Contexto) -> Resultado:
    h = Historial()
    for f in (datetime(2026, 9, 7), datetime(2026, 9, 10), datetime(2026, 8, 20)):
        h.guardar(ctx.ruta(), f)
    sem, sep, ago = h.por_semana(date(2026, 9, 9)), h.por_mes(2026, 9), h.por_mes(2026, 8)
    return ((len(sem), len(sep), len(ago)) == (2, 2, 1),
            f"3 rutas guardadas.\nSemana del 7 al 13 de septiembre: {len(sem)}\n"
            f"Septiembre 2026: {len(sep)}\nAgosto 2026: {len(ago)}")


def _hu11_c3(ctx: Contexto) -> Resultado:
    msg = Historial().listar()
    return msg == VACIO, f"Primer uso, base vacía: «{msg}»"


# ---------------------------------------------------------------- HU-12
def _hu12_c1(ctx: Contexto) -> Resultado:
    SALIDAS.mkdir(exist_ok=True)
    archivo = exportar_txt(ctx.ruta(), _lancha(), SALIDAS)
    contenido = archivo.read_text(encoding="utf-8")
    return "Distancia total" in contenido, f"Archivo descargado: {archivo.resolve()}\n\n{contenido}"


def _hu12_c2(ctx: Contexto) -> Resultado:
    texto = generar_resumen(ctx.ruta(), _lancha())
    ok = all(c in texto for c in ("Fecha:", "Hora de generación:", "Lancha asignada:"))
    return ok, "Encabezado automático:\n" + "\n".join(texto.splitlines()[:5])


def _hu12_c3(ctx: Contexto) -> Resultado:
    with mock.patch.object(Path, "write_text", side_effect=PermissionError):
        try:
            exportar_txt(ctx.ruta(), _lancha(), SALIDAS)
        except ErrorExportacion as e:
            return True, f"Error de permisos simulado.\nALERTA: {e}"
    return False, "No se mostró la alerta de permisos"


# ---------------------------------------------------------------- HU-13
def _auditoria(ctx: Contexto):
    ruta = ctx.ruta()
    ejecutada = omitir_por_clima(ruta, ruta.puntos[1].nombre)
    a = Auditoria()
    a.registrar("capitan1", "Omitir punto por clima",
                [p.nombre for p in ruta.puntos], [p.nombre for p in ejecutada.activos])
    return a


def _hu13_c1(ctx: Contexto) -> Resultado:
    entradas = _auditoria(ctx).buscar_por_fecha(date.today())
    e = entradas[0] if entradas else None
    return (len(entradas) == 1,
            f"Registro creado en segundo plano: {e.momento:%Y-%m-%d %H:%M:%S} | usuario {e.usuario} | {e.accion}"
            if e else "No se creó el registro")


def _hu13_c2(ctx: Contexto) -> Resultado:
    tabla = _auditoria(ctx).tabla_comparativa(date.today())
    return len(tabla.splitlines()) == 2, tabla


def _hu13_c3(ctx: Contexto) -> Resultado:
    a = _auditoria(ctx)
    for accion in (a.eliminar, a.modificar):
        try:
            accion(0)
            return False, "El sistema permitió alterar un registro"
        except PermissionError as e:
            msg = str(e)
    return True, f"Intento de eliminar/modificar bloqueado.\n{msg}"


# ---------------------------------------------------------------- HU-14
def _muelles(ctx: Contexto) -> Muelles:
    m = Muelles()
    m.registrar("Muelle Norte", 11.05, -74.82)
    m.registrar("Muelle Sur", 10.90, -74.80)
    m.registrar("Muelle Centro", ctx.base.lat, ctx.base.lon)
    return m


def _hu14_c1(ctx: Contexto) -> Resultado:
    plan = _muelles(ctx).planificar(ctx.copia())
    mejor = min(plan.distancias_km, key=plan.distancias_km.get)
    lineas = [f"- {n}: {d:.2f} km" for n, d in plan.distancias_km.items()]
    return plan.sugerido == mejor, "Ruta calculada desde los 3 muelles:\n" + "\n".join(lineas) + f"\nSugerido: {plan.sugerido}"


def _hu14_c2(ctx: Contexto) -> Resultado:
    plan = _muelles(ctx).planificar(ctx.copia())
    sugerido = plan.sugerido
    destino = "Muelle Sur" if sugerido != "Muelle Sur" else "Muelle Norte"
    plan.forzar(destino)
    return plan.elegido == destino, f"Sugerido: {sugerido}\nSalida forzada desde: {plan.elegido}"


def _hu14_c3(ctx: Contexto) -> Resultado:
    try:
        Muelles().registrar("Muelle lejano", 20.0, -60.0)
    except ValueError as e:
        return True, f"Registro bloqueado: «{e}»"
    return False, "El sistema aceptó un muelle fuera de la jurisdicción"


# ------------------------------------------------------------ catálogo
def _h(id_: str, titulo: str, historia: str, criterios: list[tuple[str, Callable]]) -> dict:
    return {"id": id_, "titulo": titulo, "historia": historia, "criterios": criterios}


HISTORIAS = [
    _h("HU-01", "Asignar ruta a una cuadrilla",
       "Como coordinador logístico de saneamiento, quiero asignar una ruta generada a una cuadrilla específica "
       "para llevar el control de qué equipo está ejecutando la limpieza.",
       [("Al presionar «Asignar Cuadrilla» se despliega la lista de equipos operativos disponibles.", _hu01_c1),
        ("Al asignar la ruta a la Cuadrilla Alfa, su estado cambia de «Disponible» a «En Operación».", _hu01_c2),
        ("Asignar una ruta a una cuadrilla «En Operación» es rechazado con un mensaje de advertencia.", _hu01_c3)]),
    _h("HU-02", "Ingresar coordenadas y calcular la ruta más corta",
       "Como operador de canales fluviales, quiero ingresar las coordenadas de la base y los puntos de acumulación "
       "de residuos para que la aplicación calcule de manera automatizada la ruta de navegación más corta.",
       [("Con coordenadas válidas, el sistema genera y muestra la ruta óptima.", _hu02_c1),
        ("Coordenadas fuera del área navegable bloquean la acción: «Coordenadas fuera de límite».", _hu02_c2),
        ("Con hasta 50 puntos de recolección, el resultado se muestra en máximo 2 segundos.", _hu02_c3)]),
    _h("HU-03", "Panel de control mensual",
       "Como director de sostenibilidad portuaria, quiero visualizar un panel de control con los totales acumulados "
       "de combustible ahorrado y plástico retirado mensualmente para presentar informes de los ODS.",
       [("Al seleccionar un mes se ve un gráfico de barras: gasto real vs. gasto sin el optimizador.", _hu03_c1),
        ("Un mes sin jornadas muestra los valores en cero sin que la aplicación colapse.", _hu03_c2),
        ("«Generar PDF» descarga un documento con las gráficas que se ven en pantalla.", _hu03_c3)]),
    _h("HU-04", "Ahorro frente al recorrido empírico",
       "Como entidad de saneamiento, quiero conocer el ahorro estimado frente al recorrido empírico "
       "para justificar el uso de la herramienta.",
       [("Se muestra el porcentaje de ahorro de distancia y si alcanza la meta de 15% a 20%.", _hu04_c1),
        ("Si el trayecto empírico y el calculado son iguales, el ahorro es 0% y se confirma que la ruta es óptima.", _hu04_c2),
        ("El ahorro estimado de combustible se muestra en litros.", _hu04_c3)]),
    _h("HU-05", "Omitir un punto por clima",
       "Como capitán de lancha recolectora, quiero poder omitir un punto de recolección en pleno recorrido si las "
       "condiciones de marea impiden el acceso para que el sistema me recalcule el resto del viaje.",
       [("«Omitir por clima» recalcula la distancia y une el nodo anterior con el siguiente.", _hu05_c1),
        ("El punto omitido aparece etiquetado como «Omitido» en el historial (no como completado).", _hu05_c2),
        ("Omitir la base o el nodo final se bloquea: son puntos fijos obligatorios.", _hu05_c3)]),
    _h("HU-06", "Tipo de embarcación y consumo",
       "Como operador de canales fluviales, quiero seleccionar el tipo de embarcación y su consumo promedio de "
       "combustible para que el cálculo del ahorro se ajuste a la lancha utilizada en la jornada.",
       [("Con una lancha seleccionada, la distancia del grafo se multiplica por su factor de consumo.", _hu06_c1),
        ("Sin seleccionar embarcación se usa la «Lancha Estándar» y se notifica al usuario.", _hu06_c2),
        ("Una lancha nueva (nombre, modelo y consumo por km) queda guardada permanentemente en el catálogo.", _hu06_c3)]),
    _h("HU-07", "Registrar kilogramos recolectados",
       "Como analista ambiental, quiero registrar la cantidad (en kg) de residuos recolectados en cada punto de la "
       "ruta para poder generar estadísticas del volumen de contaminación.",
       [("Al completar un punto aparece un campo obligatorio para el peso en kilogramos.", _hu07_c1),
        ("Un valor negativo o letras en el peso producen el error «Formato inválido».", _hu07_c2),
        ("Al cerrar la jornada se calcula y muestra el total de kilogramos recolectados.", _hu07_c3)]),
    _h("HU-08", "Validar los datos de entrada",
       "Como vigía de la embarcación, quiero que se validen mis datos de entrada para evitar resultados erróneos y "
       "asegurar la integridad de los cálculos del sistema.",
       [("Un dato vacío, duplicado o fuera de rango muestra cuál falló y no ejecuta el cálculo.", _hu08_c1),
        ("Coordenadas con letras o caracteres especiales se bloquean con un error de sintaxis inmediato.", _hu08_c2),
        ("Con todos los campos correctos se habilita el botón de cálculo sin advertencias.", _hu08_c3)]),
    _h("HU-09", "Alerta de combustible",
       "Como supervisor de flota marina, quiero que el sistema me advierta si la distancia del recorrido calculado "
       "excede la capacidad máxima del tanque de la lancha para evitar que quede varada.",
       [("Si el consumo supera el 100% del tanque, se muestra el banner rojo «Peligro: Combustible Insuficiente».", _hu09_c1),
        ("La alerta roja sugiere dividir la ruta en dos días o cambiar a una lancha de mayor capacidad.", _hu09_c2),
        ("Entre el 85% y el 99% del tanque se muestra la alerta amarilla «Nivel de combustible al límite».", _hu09_c3)]),
    _h("HU-10", "Tipo de residuo predominante",
       "Como analista ambiental, quiero etiquetar cada punto de recolección con el tipo de residuo predominante "
       "(plásticos, madera, metales) para entender qué contaminación afecta más cada sector.",
       [("Al completar un punto hay un menú obligatorio: Plásticos, Maderas/Orgánicos y Metales/Vidrios.", _hu10_c1),
        ("El filtro «Plásticos» del historial solo muestra rutas y nodos con ese residuo predominante.", _hu10_c2),
        ("El reporte desglosa el porcentaje del peso total por tipo de material.", _hu10_c3)]),
    _h("HU-11", "Historial de rutas",
       "Como operador de canales fluviales, quiero consultar un historial de rutas generadas previamente para "
       "comparar los trayectos ejecutados en semanas anteriores.",
       [("El historial lista fechas, distancias y puntos de recolección anteriores.", _hu11_c1),
        ("El filtro de calendario muestra solo los recorridos de la semana o mes seleccionado.", _hu11_c2),
        ("Con la base vacía se muestra «No hay rutas registradas hasta el momento».", _hu11_c3)]),
    _h("HU-12", "Exportar resumen en texto",
       "Como autoridad portuaria, quiero exportar un resumen en formato de texto con los detalles de la ruta óptima "
       "para adjuntarlo formalmente a los informes operativos de las jornadas de saneamiento.",
       [("Al exportar se descarga un archivo de texto con las coordenadas y distancias totales.", _hu12_c1),
        ("El documento tiene un encabezado automático con fecha, hora de generación y lancha asignada.", _hu12_c2),
        ("Ante un error de permisos se alerta al usuario sugiriendo cambiar la carpeta de destino.", _hu12_c3)]),
    _h("HU-13", "Registro de auditoría",
       "Como autoridad portuaria, quiero un registro de auditoría que guarde cualquier alteración manual hecha por "
       "los operadores a las rutas aprobadas para mantener la transparencia en el uso de los recursos.",
       [("Cada cambio manual crea un registro invisible para el operador, con fecha, hora y usuario.", _hu13_c1),
        ("La pestaña «Auditoría» compara la «Ruta planificada inicialmente» con la «Ruta ejecutada».", _hu13_c2),
        ("Eliminar o alterar un registro de auditoría se deniega: son de solo lectura.", _hu13_c3)]),
    _h("HU-14", "Múltiples muelles de salida",
       "Como coordinador logístico de saneamiento, quiero registrar múltiples muelles de salida para que el sistema "
       "me sugiera desde cuál es más corto despachar la lancha.",
       [("Con 3 muelles guardados, el sistema calcula desde los 3 y sugiere el de menor distancia total.", _hu14_c1),
        ("Un menú permite forzar la salida desde otro muelle (por ejemplo, «Muelle Sur»).", _hu14_c2),
        ("Un muelle fuera de los límites marítimos se rechaza con «Ubicación fuera de rango».", _hu14_c3)]),
]


def ejecutar_criterio(funcion: Callable[[Contexto], Resultado], ctx: Contexto) -> Resultado:
    try:
        return funcion(ctx)
    except Exception as e:  # el simulador debe mostrar el fallo, no cerrarse
        return False, f"Error inesperado: {type(e).__name__}: {e}"


def ejecutar_todos(ctx: Contexto) -> list[tuple[str, int, str, bool, str]]:
    salida = []
    for h in HISTORIAS:
        for n, (desc, fn) in enumerate(h["criterios"], 1):
            ok, texto = ejecutar_criterio(fn, ctx)
            salida.append((h["id"], n, desc, ok, texto))
    return salida
