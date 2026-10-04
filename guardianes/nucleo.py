from __future__ import annotations

import math
from dataclasses import dataclass, field

RADIO_TIERRA_KM = 6371.0088

# Area navegable mapeada (lat_min, lat_max, lon_min, lon_max): Barranquilla - Bocas de Ceniza.
# Es un valor de ejemplo; se puede ajustar a la jurisdiccion real.
LIMITES_NAVEGABLES = (10.80, 11.15, -75.00, -74.65)

TIPOS_RESIDUO = ("Plásticos", "Maderas/Orgánicos", "Metales/Vidrios")

PENDIENTE = "Pendiente"
COMPLETADO = "Completado"
OMITIDO = "Omitido"


def dentro_de_limites(lat: float, lon: float) -> bool:
    lat_min, lat_max, lon_min, lon_max = LIMITES_NAVEGABLES
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


@dataclass
class Punto:
    nombre: str
    lat: float
    lon: float
    kg: float = 0.0
    residuo: str | None = None
    estado: str = PENDIENTE


def distancia_km(a: Punto, b: Punto) -> float:
    f1, f2 = math.radians(a.lat), math.radians(b.lat)
    h = (math.sin((f2 - f1) / 2) ** 2
         + math.cos(f1) * math.cos(f2) * math.sin(math.radians(b.lon - a.lon) / 2) ** 2)
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(h))


def longitud_ruta(origen: Punto, puntos: list[Punto], destino: Punto | None = None) -> float:
    destino = destino or origen
    camino = [origen, *puntos, destino]
    return sum(distancia_km(camino[i], camino[i + 1]) for i in range(len(camino) - 1))


def vecino_mas_cercano(origen: Punto, puntos: list[Punto]) -> list[Punto]:
    pendientes, orden, actual = list(puntos), [], origen
    while pendientes:
        siguiente = min(pendientes, key=lambda p: distancia_km(actual, p))
        pendientes.remove(siguiente)
        orden.append(siguiente)
        actual = siguiente
    return orden


def dos_opt(origen: Punto, puntos: list[Punto], destino: Punto | None = None) -> list[Punto]:
    destino = destino or origen
    nodos = [origen, *puntos, destino]
    n = len(puntos)
    d = [[distancia_km(a, b) for b in nodos] for a in nodos]
    camino = list(range(n + 2))
    mejoro = True
    while mejoro:
        mejoro = False
        for i in range(1, n):
            for j in range(i + 1, n + 1):
                a, b, c, e = camino[i - 1], camino[i], camino[j], camino[j + 1]
                if d[a][c] + d[b][e] < d[a][b] + d[c][e] - 1e-9:
                    camino[i:j + 1] = camino[i:j + 1][::-1]
                    mejoro = True
    return [nodos[k] for k in camino[1:-1]]


def optimizar_ruta(origen: Punto, puntos: list[Punto], destino: Punto | None = None) -> list[Punto]:
    return dos_opt(origen, vecino_mas_cercano(origen, puntos), destino)


@dataclass
class Ruta:
    id: str
    base: Punto
    puntos: list[Punto] = field(default_factory=list)

    @property
    def activos(self) -> list[Punto]:
        return [p for p in self.puntos if p.estado != OMITIDO]

    @property
    def distancia_km(self) -> float:
        return longitud_ruta(self.base, self.activos)

    def detalle(self) -> list[str]:
        lineas = [f"Base: {self.base.nombre} ({self.base.lat}, {self.base.lon})"]
        for i, p in enumerate(self.puntos, 1):
            marca = " [Omitido]" if p.estado == OMITIDO else ""
            lineas.append(f"{i}. {p.nombre} ({p.lat}, {p.lon}){marca}")
        return lineas


@dataclass(frozen=True)
class Embarcacion:
    nombre: str
    modelo: str
    consumo_l_km: float
    tanque_l: float = 100.0

    def combustible_para(self, distancia_km: float) -> float:
        return distancia_km * self.consumo_l_km
