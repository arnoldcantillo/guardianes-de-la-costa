from datetime import date

from guardianes.hu01_asignar_cuadrilla import Cuadrilla, Despacho
from guardianes.hu02_coordenadas import calcular_ruta, crear_punto
from guardianes.hu03_panel import Jornada, PanelControl
from guardianes.hu04_ahorro import estimar_ahorro
from guardianes.hu05_omitir_punto import omitir_por_clima
from guardianes.hu06_embarcacion import Catalogo
from guardianes.hu07_registro_kg import RegistroJornada
from guardianes.hu08_validacion import exigir_validos
from guardianes.hu09_alerta_combustible import evaluar_combustible
from guardianes.hu11_historial import Historial
from guardianes.hu12_exportar import generar_resumen
from guardianes.hu13_auditoria import Auditoria
from guardianes.hu14_muelles import Muelles


def main() -> None:
    muelles = Muelles()
    muelles.registrar("Muelle Norte", 11.05, -74.82)
    muelles.registrar("Muelle Sur", 10.90, -74.80)
    base = crear_punto("Muelle Centro", 10.96, -74.80)
    puntos = [crear_punto("Dársena 1", 10.99, -74.85), crear_punto("Desembocadura", 10.93, -74.78),
              crear_punto("Canal Norte", 11.02, -74.79), crear_punto("Muelle viejo", 10.95, -74.88)]

    exigir_validos(base, puntos)
    plan = muelles.planificar(puntos)
    print("Muelle sugerido:", plan.sugerido, {k: round(v, 1) for k, v in plan.distancias_km.items()})

    lancha, aviso = Catalogo().seleccionar(None)
    print("Aviso:", aviso)
    ruta = calcular_ruta(base, puntos)
    print("\n".join(ruta.detalle()), f"\nDistancia: {ruta.distancia_km:.2f} km")
    print(estimar_ahorro(base, puntos, lancha, ruta.puntos).reporte())
    print("Alerta:", evaluar_combustible(lancha, ruta.distancia_km).mensaje)

    despacho = Despacho([Cuadrilla("Alfa"), Cuadrilla("Beta")])
    despacho.asignar(ruta, "Alfa")
    print("Panel general:", despacho.panel_general())

    auditoria = Auditoria()
    original = [p.nombre for p in ruta.puntos]
    ruta = omitir_por_clima(ruta, ruta.puntos[1].nombre)
    auditoria.registrar("capitan1", "Omitir por clima", original, [p.nombre for p in ruta.activos])

    jornada = RegistroJornada(ruta)
    for p in ruta.activos:
        jornada.completar_punto(p.nombre, 12.5, "Plásticos")
    total = jornada.cerrar_jornada()
    print(f"Total recolectado: {total} kg")

    historial = Historial()
    historial.guardar(ruta)
    print(historial.listar())

    panel = PanelControl()
    panel.registrar(Jornada(date.today(), 40, 52, total))
    print(panel.grafico_barras(date.today().year, date.today().month))
    print(auditoria.tabla_comparativa(date.today()))
    print(generar_resumen(ruta, lancha))


if __name__ == "__main__":
    main()
