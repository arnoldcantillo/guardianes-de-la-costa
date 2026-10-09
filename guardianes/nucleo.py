from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

RADIO_TIERRA_KM = 6371.0088

# Area navegable mapeada (lat_min, lat_max, lon_min, lon_max): Barranquilla - Bocas de Ceniza.
# Es un valor de ejemplo; se puede ajustar a la jurisdiccion real.
LIMITES_NAVEGABLES = (10.80, 11.15, -75.00, -74.65)

# Cada nodo se conecta con sus k vecinos más cercanos al construir el grafo de navegación.
VECINOS_POR_NODO = 2

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


class Grafo:
    """Grafo no dirigido de navegación.

    Los nodos son la base y los puntos de acumulación. Cada nodo se une con sus
    ``k`` vecinos más cercanos y el peso de cada arista es la distancia Haversine.
    Si quedan zonas aisladas, se unen con la arista más corta entre ellas. El
    resultado no depende del orden en que se pasen los nodos.
    """

    def __init__(self, nodos: list[Punto], k: int = VECINOS_POR_NODO):
        self.nodos = list(nodos)
        n = len(self.nodos)
        self.ady: list[dict[int, float]] = [{} for _ in range(n)]
        d = [[distancia_km(a, b) for b in self.nodos] for a in self.nodos]

        def clave(j: int):
            p = self.nodos[j]
            return (p.nombre, p.lat, p.lon, j)

        for i in range(n):
            cercanos = sorted((j for j in range(n) if j != i), key=lambda j: (d[i][j], clave(j)))[:k]
            for j in cercanos:
                self._unir(i, j, d[i][j])
        self._conectar_zonas(d)

    def _unir(self, i: int, j: int, peso: float) -> None:
        self.ady[i][j] = peso
        self.ady[j][i] = peso

    def _zonas(self) -> list[int]:
        zona = [-1] * len(self.nodos)
        for inicio in range(len(self.nodos)):
            if zona[inicio] != -1:
                continue
            zona[inicio] = inicio
            pila = [inicio]
            while pila:
                u = pila.pop()
                for v in self.ady[u]:
                    if zona[v] == -1:
                        zona[v] = inicio
                        pila.append(v)
        return zona

    def _conectar_zonas(self, d: list[list[float]]) -> None:
        n = len(self.nodos)
        while True:
            zona = self._zonas()
            if len(set(zona)) <= 1:
                return
            i, j = min(((a, b) for a in range(n) for b in range(a + 1, n) if zona[a] != zona[b]),
                       key=lambda par: (d[par[0]][par[1]], par))
            self._unir(i, j, d[i][j])


def dijkstra(grafo: Grafo, origen: int) -> tuple[list[float], list[int | None]]:
    """Camino mínimo desde ``origen`` hacia todos los nodos. Devuelve (distancias, previos)."""
    n = len(grafo.nodos)
    dist = [math.inf] * n
    previo: list[int | None] = [None] * n
    dist[origen] = 0.0
    cola = [(0.0, origen)]
    while cola:
        du, u = heapq.heappop(cola)
        if du > dist[u]:
            continue
        for v, peso in grafo.ady[u].items():
            nueva = du + peso
            if nueva < dist[v] - 1e-12:
                dist[v] = nueva
                previo[v] = u
                heapq.heappush(cola, (nueva, v))
    return dist, previo


def camino_minimo(grafo: Grafo, a: int, b: int) -> tuple[float, list[int]]:
    """Distancia y lista de nodos del camino mínimo entre ``a`` y ``b``."""
    dist, previo = dijkstra(grafo, a)
    camino, actual = [b], b
    while actual != a:
        actual = previo[actual]
        camino.append(actual)
    return dist[b], camino[::-1]


def _grafo_de(nodos: list[Punto]) -> tuple[Grafo, list[int]]:
    """Grafo con los nodos sin repetir (por identidad) y la posición de cada uno en ``nodos``."""
    unicos: list[Punto] = []
    pos: list[int] = []
    for p in nodos:
        for k, u in enumerate(unicos):
            if u is p:
                pos.append(k)
                break
        else:
            unicos.append(p)
            pos.append(len(unicos) - 1)
    return Grafo(unicos), pos


def matriz_distancias(nodos: list[Punto]) -> list[list[float]]:
    """Distancia de camino mínimo (Dijkstra) entre cada par de nodos de la lista."""
    grafo, pos = _grafo_de(nodos)
    por_nodo = [dijkstra(grafo, i)[0] for i in range(len(grafo.nodos))]
    return [[por_nodo[a][b] for b in pos] for a in pos]


def longitud_ruta(origen: Punto, puntos: list[Punto], destino: Punto | None = None) -> float:
    destino = destino or origen
    camino = [origen, *puntos, destino]
    d = matriz_distancias(camino)
    return sum(d[i][i + 1] for i in range(len(camino) - 1))


def tramos_ruta(origen: Punto, puntos: list[Punto], destino: Punto | None = None) -> list[dict]:
    """Detalle de cada tramo: nodos por los que pasa el camino mínimo y su distancia."""
    destino = destino or origen
    camino = [origen, *puntos, destino]
    grafo, pos = _grafo_de(camino)
    salida = []
    for i in range(len(camino) - 1):
        km, nodos = camino_minimo(grafo, pos[i], pos[i + 1])
        salida.append({"desde": camino[i], "hasta": camino[i + 1], "km": km,
                       "pasa_por": [grafo.nodos[k] for k in nodos[1:-1]],
                       "nodos": [grafo.nodos[k] for k in nodos]})
    return salida


def vecino_mas_cercano(origen: Punto, puntos: list[Punto]) -> list[Punto]:
    nodos = [origen, *puntos]
    d = matriz_distancias(nodos)
    pendientes, orden, actual = list(range(1, len(nodos))), [], 0
    while pendientes:
        siguiente = min(pendientes, key=lambda k: d[actual][k])
        pendientes.remove(siguiente)
        orden.append(nodos[siguiente])
        actual = siguiente
    return orden


def dos_opt(origen: Punto, puntos: list[Punto], destino: Punto | None = None) -> list[Punto]:
    destino = destino or origen
    nodos = [origen, *puntos, destino]
    n = len(puntos)
    d = matriz_distancias(nodos)
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
    """Orden de visita: distancias por Dijkstra, vecino más cercano y mejora 2-opt."""
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
