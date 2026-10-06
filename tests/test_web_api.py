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


if __name__ == "__main__":
    unittest.main()
