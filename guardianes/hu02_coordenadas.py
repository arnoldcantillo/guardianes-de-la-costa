from __future__ import annotations

import time

from .nucleo import Punto, Ruta, dentro_de_limites, optimizar_ruta


class CoordenadasFueraDeLimite(ValueError):
    def __init__(self) -> None:
        super().__init__("Coordenadas fuera de límite")


def crear_punto(nombre: str, lat: float, lon: float) -> Punto:
    if not dentro_de_limites(lat, lon):
        raise CoordenadasFueraDeLimite()
    return Punto(nombre, lat, lon)


def calcular_ruta(base: Punto, puntos: list[Punto], ruta_id: str = "R-001") -> Ruta:
    for p in (base, *puntos):
        if not dentro_de_limites(p.lat, p.lon):
            raise CoordenadasFueraDeLimite()
    if not puntos:
        raise ValueError("Debe ingresar al menos un punto de recolección")
    return Ruta(ruta_id, base, optimizar_ruta(base, puntos))


def calcular_ruta_cronometrada(base: Punto, puntos: list[Punto]) -> tuple[Ruta, float]:
    inicio = time.perf_counter()
    ruta = calcular_ruta(base, puntos)
    return ruta, time.perf_counter() - inicio
