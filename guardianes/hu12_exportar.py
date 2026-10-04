from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .hu10_tipo_residuo import desglose_porcentual
from .nucleo import Embarcacion, Ruta


class ErrorExportacion(Exception):
    pass


def generar_resumen(ruta: Ruta, embarcacion: Embarcacion, ahora: datetime | None = None) -> str:
    ahora = ahora or datetime.now()
    lineas = [
        "RESUMEN DE RUTA ÓPTIMA",
        f"Fecha: {ahora:%Y-%m-%d}",
        f"Hora de generación: {ahora:%H:%M:%S}",
        f"Lancha asignada: {embarcacion.nombre} ({embarcacion.modelo})",
        f"Ruta: {ruta.id}",
        "",
        *ruta.detalle(),
        "",
        f"Distancia total: {ruta.distancia_km:.2f} km",
        f"Combustible estimado: {embarcacion.combustible_para(ruta.distancia_km):.2f} L",
    ]
    desglose = desglose_porcentual(ruta.puntos)
    if any(desglose.values()):
        lineas += ["", "Residuos por tipo (% del peso total):"]
        lineas += [f"- {tipo}: {pct}%" for tipo, pct in desglose.items()]
    return "\n".join(lineas) + "\n"


def exportar_txt(ruta: Ruta, embarcacion: Embarcacion, carpeta: str | Path) -> Path:
    destino = Path(carpeta) / f"ruta_{ruta.id}.txt"
    try:
        destino.write_text(generar_resumen(ruta, embarcacion), encoding="utf-8")
    except PermissionError:
        raise ErrorExportacion(
            f"No hay permisos para escribir en {carpeta}. Cambie la carpeta de destino.") from None
    return destino
