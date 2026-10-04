from __future__ import annotations

from dataclasses import dataclass

from .nucleo import Embarcacion

ROJO, AMARILLO, VERDE = "rojo", "amarillo", "verde"


@dataclass(frozen=True)
class Alerta:
    color: str
    porcentaje_tanque: float
    mensaje: str
    sugerencia: str | None = None


def evaluar_combustible(embarcacion: Embarcacion, distancia_km: float) -> Alerta:
    pct = 100 * embarcacion.combustible_para(distancia_km) / embarcacion.tanque_l
    if pct > 100:
        return Alerta(ROJO, pct, "Peligro: Combustible Insuficiente",
                      "Divida la ruta en dos días o cambie a una lancha de mayor capacidad.")
    if pct >= 85:
        return Alerta(AMARILLO, pct, "Nivel de combustible al límite")
    return Alerta(VERDE, pct, "Combustible suficiente")
