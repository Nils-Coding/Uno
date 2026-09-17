"""Prüft Übergänge, verdeckte Hände und die Siegesserie mit echten Spielzügen."""

import os
from pathlib import Path
from random import Random
import tempfile
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from Kartenspiel.karte import Karte
from Kartenspiel.sonderkarte import Sonderkarte
from Kartenspiel.spiel import Spiel
from Kartenspiel.ui.anwendung import Anwendung
from Kartenspiel.ui.audio import Soundmanager


class SpielgefuehlTest(unittest.TestCase):
    def setUp(self):
        self.ordner = tempfile.TemporaryDirectory()
        self.app = Anwendung(Spiel(Random(7)), Soundmanager(Path(self.ordner.name) / "audio.json"))
        self.app.aktion("anzahl", 2)
        self.starten()

    def tearDown(self):
        pygame.quit()
        self.ordner.cleanup()

    def starten(self):
        self.app.aktion("starten")
        self.app.aktion("mischen_beenden")
        self.app.aktion("bereit")
        self.app.spiel.stapel.setAbgelegt([Karte("rot", "5")])

    def test_sonderkarteneffekt_blockiert_eingaben_bis_zum_ende(self):
        self.app.spiel.aktueller_spieler.setKarten([
            Sonderkarte("rot", "2", "ziehen"), Karte("blau", "1"), Karte("grün", "3")])
        self.app.aktion("legen", 0)
        self.app.aktualisieren(0.4)
        self.assertEqual(self.app.effekt.titel, "+2")
        self.assertEqual(self.app.phase, "animation")
        anzahl = [len(hand) for hand in self.app.spiel.spieler]
        self.app.aktion("ziehen")
        self.app.aktion("legen", 0)
        self.assertEqual([len(hand) for hand in self.app.spiel.spieler], anzahl)
        self.app.aktualisieren(1.04)
        self.assertIsNone(self.app.animation)
        # Bei zwei Spielern geht +2 zurück an denselben Spieler.
        self.assertEqual(self.app.phase, "spielen")

    def test_handoff_enthaelt_keine_anklickbaren_handkarten(self):
        self.app.spiel.aktueller_spieler.setKarten([
            Karte("rot", "7"), Karte("blau", "1"), Karte("grün", "3")])
        self.app.aktion("legen", 0)
        self.app.aktualisieren(0.56)
        self.app.ansicht.zeichnen(self.app)
        self.assertEqual(self.app.phase, "uebergabe")
        self.assertFalse(self.app.ansicht.karten)
        self.assertEqual([b.aktion for b in self.app.ansicht.buttons], ["bereit"])
        self.app.aktion("bereit")
        self.app.ansicht.zeichnen(self.app)
        self.assertEqual(len(self.app.ansicht.karten), len(self.app.spiel.aktueller_spieler))

    def test_sieg_wird_einmal_gezaehlt_und_revanche_behaelt_serie(self):
        self.app.spiel.aktueller_spieler.setKarten([Karte("rot", "7")])
        self.app.aktion("legen", 0)
        self.app.aktualisieren(0.4)
        self.assertEqual(self.app.siege, {1: 1})
        self.app.aktualisieren(5)
        self.assertEqual(self.app.siege, {1: 1})
        self.starten()
        self.assertEqual(self.app.siege, {1: 1})
        self.assertEqual(self.app.aktionen, 0)
        self.assertFalse(self.app.verlauf)
        self.app.aktion("pause")
        self.app.aktion("neustart")
        self.app.aktion("anzahl", 3)
        self.app.aktion("starten")
        self.assertFalse(self.app.siege)

    def test_ziehverlauf_verraet_keine_geheime_karte(self):
        self.app.spiel.stapel.setVerdeckt([Karte("grün", "9")])
        self.app.aktion("ziehen")
        self.assertEqual(self.app.verlauf[-1][1], "zieht eine Karte")
        self.assertNotIn("9", repr(self.app.verlauf))

    def test_pausenzeit_wird_nicht_als_spielzeit_gezaehlt(self):
        self.app.aktualisieren(2)
        self.app.aktion("pause")
        vorher = self.app.spielzeit
        self.app.aktualisieren(60)
        self.assertEqual(self.app.spielzeit, vorher)


if __name__ == "__main__":
    unittest.main()
