"""Prüft den installierten Startbefehl ohne Importe aus dem Arbeitsordner."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class InstallationTest(unittest.TestCase):
    def test_installierter_startbefehl_oeffnet_die_oberflaeche(self):
        # -I und ein fremder Arbeitsordner verhindern, dass der Quellordner
        # eine defekte Installation verdeckt. Nur das Beenden wird automatisiert.
        programm = """
import runpy
import sysconfig
from pathlib import Path
from unittest.mock import patch
import pygame

startbefehl = Path(sysconfig.get_path('scripts')) / 'uno-ui'
with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.QUIT)]):
    runpy.run_path(str(startbefehl), run_name='__main__')
"""
        umgebung = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        with tempfile.TemporaryDirectory() as ordner:
            ergebnis = subprocess.run(
                [sys.executable, "-I", "-c", programm],
                cwd=Path(ordner),
                env=umgebung,
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(ergebnis.returncode, 0, ergebnis.stdout + ergebnis.stderr)


if __name__ == "__main__":
    unittest.main()
