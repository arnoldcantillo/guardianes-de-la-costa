from __future__ import annotations

from dataclasses import dataclass

from .nucleo import Punto, dentro_de_limites, longitud_ruta, optimizar_ruta


@dataclass
class Plan:
    sugerido: str
    distancias_km: dict[str, float]
    elegido: str

    def forzar(self, nombre_muelle: str) -> None:
        if nombre_muelle not in self.distancias_km:
            raise ValueError(f"El muelle {nombre_muelle} no está registrado")
        self.elegido = nombre_muelle


class Muelles:
    def __init__(self) -> None:
        self.items: dict[str, Punto] = {}

    def registrar(self, nombre: str, lat: float, lon: float) -> Punto:
        if not dentro_de_limites(lat, lon):
            raise ValueError("Ubicación fuera de rango")
        muelle = Punto(nombre, lat, lon)
        self.items[nombre] = muelle
        return muelle

    def planificar(self, puntos: list[Punto]) -> Plan:
        if not self.items:
            raise ValueError("No hay muelles registrados")
        distancias = {n: longitud_ruta(m, optimizar_ruta(m, puntos)) for n, m in self.items.items()}
        mejor = min(distancias, key=distancias.get)
        return Plan(mejor, distancias, mejor)
