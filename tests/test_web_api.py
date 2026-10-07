import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardianes import web_api

ESCENARIO = {"base": {"nombre": "Muelle Centro", "lat": 10.96, "lon": -74.80},
             "puntos": [{"nombre": "A", "lat": 10.99, "lon": -74.85}, {"nombre": "B", "lat": 10.93, "lon": -74.78},
                        {"nombre": "C", "lat": 11.02, "lon": -74.79}]}


class TestWebApi(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_catalogo(self):
        cat = json.loads(web_api.catalogo())
        self.assertEqual(len(cat), 14)
        self.assertTrue(all(len(h["criterios"]) == 3 for h in cat))

    def test_escenario_valido_e_invalido(self):
        r = json.loads(web_api.aplicar_escenario(json.dumps(ESCENARIO)))
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["mapa"]["ruta"]), 3)
        malo = {**ESCENARIO, "puntos": [{"nombre": "A", "lat": 40, "lon": -3.7}]}
        self.assertFalse(json.loads(web_api.aplicar_escenario(json.dumps(malo)))["ok"])
        self.assertFalse(json.loads(web_api.aplicar_escenario("{}"))["ok"])

    def test_ejecutar_y_archivos(self):
        esc = json.dumps(ESCENARIO)
        r = json.loads(web_api.ejecutar(2, 2, esc))      # HU-03 criterio 3: genera el PDF
        self.assertTrue(r["ok"])
        self.assertEqual([a["nombre"] for a in r["archivos"]], ["panel_septiembre_2026.pdf"])
        r = json.loads(web_api.ejecutar(8, 0, esc))      # HU-09: no genera archivos
        self.assertEqual(r["archivos"], [])

    def test_bloques_hu03_y_tablas(self):
        esc = json.dumps(ESCENARIO)
        r = json.loads(web_api.ejecutar(2, 0, esc))       # HU-03 criterio 1: gráfico de barras
        self.assertTrue(r["ok"])
        barras = next(b for b in r["bloques"] if b["t"] == "barras")
        self.assertEqual({x["etiqueta"]: x["valor"] for x in barras["barras"]},
                         {"Con optimizador": 140, "Sin optimizador": 175})
        r = json.loads(web_api.ejecutar(2, 1, esc))       # enero vacío: todo en cero
        self.assertTrue(r["ok"])
        barras = next(b for b in r["bloques"] if b["t"] == "barras")
        self.assertTrue(all(x["valor"] == 0 for x in barras["barras"]))
        r = json.loads(web_api.ejecutar(10, 0, esc))      # HU-11 criterio 1: tabla del historial
        self.assertEqual(next(b for b in r["bloques"] if b["t"] == "tabla")["cabeceras"][0], "Fecha")

    def test_ruta_del_escenario_trae_tabla_y_mapa(self):
        r = json.loads(web_api.aplicar_escenario(json.dumps(ESCENARIO)))
        self.assertIn("tabla", [b["t"] for b in r["bloques"]])
        self.assertEqual(len(r["mapa"]["ruta"]), 3)


if __name__ == "__main__":
    unittest.main()
