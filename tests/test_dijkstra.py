import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardianes.nucleo import (Grafo, Punto, camino_minimo, dijkstra, distancia_km, longitud_ruta,
                               matriz_distancias, optimizar_ruta, tramos_ruta)


def _puntos(n: int, semilla: int = 1) -> list[Punto]:
    azar = random.Random(semilla)
    return [Punto(f"P{i}", 10.85 + azar.random() * 0.25, -74.95 + azar.random() * 0.25) for i in range(n)]


def _floyd(grafo: Grafo) -> list[list[float]]:
    n = len(grafo.nodos)
    d = [[0.0 if i == j else grafo.ady[i].get(j, math.inf) for j in range(n)] for i in range(n)]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


class TestDijkstra(unittest.TestCase):
    def test_grafo_conectado_y_simetrico(self):
        g = Grafo(_puntos(12))
        for i, vecinos in enumerate(g.ady):
            self.assertTrue(vecinos)
            for j, peso in vecinos.items():
                self.assertEqual(g.ady[j][i], peso)
        dist, _ = dijkstra(g, 0)
        self.assertTrue(all(math.isfinite(x) for x in dist))

    def test_coincide_con_floyd_warshall(self):
        g = Grafo(_puntos(15, semilla=7))
        esperado = _floyd(g)
        for i in range(len(g.nodos)):
            dist, _ = dijkstra(g, i)
            for j, x in enumerate(dist):
                self.assertAlmostEqual(x, esperado[i][j], places=9)

    def test_camino_minimo_suma_sus_aristas(self):
        g = Grafo(_puntos(10, semilla=3))
        km, nodos = camino_minimo(g, 0, 9)
        self.assertEqual(nodos[0], 0)
        self.assertEqual(nodos[-1], 9)
        self.assertAlmostEqual(km, sum(g.ady[a][b] for a, b in zip(nodos, nodos[1:])))

    def test_camino_no_es_mas_corto_que_la_linea_recta(self):
        pts = _puntos(10, semilla=5)
        m = matriz_distancias(pts)
        for i, a in enumerate(pts):
            for j, b in enumerate(pts):
                self.assertGreaterEqual(m[i][j] + 1e-9, distancia_km(a, b))

    def test_camino_con_desvio_en_cadena(self):
        # Cuatro puntos casi en línea: con k=1 el grafo es una cadena y el camino A-D pasa por B y C.
        a, b, c, d = (Punto("A", 10.90, -74.90), Punto("B", 10.92, -74.90),
                      Punto("C", 10.94, -74.90), Punto("D", 10.96, -74.90))
        g = Grafo([a, b, c, d], k=1)
        km, nodos = camino_minimo(g, 0, 3)
        self.assertEqual(nodos, [0, 1, 2, 3])
        self.assertAlmostEqual(km, distancia_km(a, d), places=6)

    def test_no_depende_del_orden_de_entrada(self):
        pts = _puntos(9, semilla=11)
        base = pts[0]
        a = longitud_ruta(base, optimizar_ruta(base, pts[1:]))
        b = longitud_ruta(base, optimizar_ruta(base, list(reversed(pts[1:]))))
        self.assertAlmostEqual(a, b, places=6)

    def test_tramos_reconstruyen_la_distancia_total(self):
        pts = _puntos(8, semilla=2)
        base, resto = pts[0], optimizar_ruta(pts[0], pts[1:])
        tramos = tramos_ruta(base, resto)
        self.assertEqual(len(tramos), len(resto) + 1)
        self.assertAlmostEqual(sum(t["km"] for t in tramos), longitud_ruta(base, resto))
        self.assertIs(tramos[0]["desde"], base)
        self.assertIs(tramos[-1]["hasta"], base)

    def test_la_ruta_optimizada_visita_todos_los_puntos_una_vez(self):
        pts = _puntos(10, semilla=4)
        orden = optimizar_ruta(pts[0], pts[1:])
        self.assertEqual(sorted(p.nombre for p in orden), sorted(p.nombre for p in pts[1:]))


if __name__ == "__main__":
    unittest.main()
