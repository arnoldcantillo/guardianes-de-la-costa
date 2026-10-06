import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardianes import escenarios
from guardianes.escenarios import Contexto, HISTORIAS, ejecutar_todos


class TestEscenarios(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_catalogo_completo(self):
        self.assertEqual(len(HISTORIAS), 14)
        self.assertTrue(all(len(h["criterios"]) == 3 for h in HISTORIAS))

    def test_los_42_criterios_cumplen(self):
        fallos = [(i, n, t) for i, n, _, ok, t in ejecutar_todos(Contexto.por_defecto()) if not ok]
        self.assertEqual(fallos, [])


if __name__ == "__main__":
    unittest.main()
