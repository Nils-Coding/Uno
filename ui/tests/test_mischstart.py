import os
import unittest
from random import Random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from Kartenspiel.spiel import Spiel
from Kartenspiel.stapel import MISCHVERFAHREN
from Kartenspiel.ui.anwendung import Anwendung


def kartenstand(spiel):
    return (
        [[str(karte) for karte in hand.getKarten()] for hand in spiel.spieler],
        [str(karte) for karte in spiel.stapel.getVerdeckt()],
        [str(karte) for karte in spiel.stapel.getAbgelegt()],
    )


class MischstartTest(unittest.TestCase):
    def setUp(self):
        self.app = Anwendung(Spiel(Random(42)))

    def tearDown(self):
        pygame.quit()

    def test_jedes_verfahren_startet_nach_animation_mit_richtigen_karten(self):
        for index, verfahren in enumerate(MISCHVERFAHREN):
            with self.subTest(verfahren=verfahren):
                self.app.spiel = Spiel(Random(42))
                self.app.phase = "start"
                self.app.aktion("mischen", index)
                self.app.aktion("anzahl", 10)
                self.app.aktion("starten")
                self.assertEqual(self.app.phase, "mischen")
                self.assertEqual(self.app.spiel.spieler, ())
                animation = self.app.mischanimation
                self.assertEqual(animation.verfahren, verfahren)
                self.app.aktualisieren(animation.dauer - 0.01)
                self.assertEqual(self.app.phase, "mischen")
                self.app.aktualisieren(0.02)
                self.assertEqual(self.app.phase, "uebergabe")
                self.assertIsNone(self.app.mischanimation)
                erwartet = Spiel(Random(42))
                erwartet.starten(10, verfahren)
                self.assertEqual(kartenstand(self.app.spiel), kartenstand(erwartet))
                self.assertTrue(all(len(hand) == 7 for hand in self.app.spiel.spieler))
                self.app.zeichnen()
                self.app.aktion("bereit")
                self.app.zeichnen()
                self.assertEqual(self.app.phase, "spielen")

    def test_ueberspringen_mischt_genau_einmal_auch_bei_weiteren_events(self):
        for index, verfahren in enumerate(MISCHVERFAHREN):
            with self.subTest(verfahren=verfahren):
                self.app.spiel = Spiel(Random(42))
                self.app.phase = "start"
                self.app.aktion("mischen", index)
                self.app.aktion("anzahl", 2)
                runde = self.app.runde
                self.app.aktion("starten")
                self.app.aktualisieren(0.8)
                self.app.aktion("mischen_beenden")
                erwartet = Spiel(Random(42))
                erwartet.starten(2, verfahren)
                self.assertEqual(kartenstand(self.app.spiel), kartenstand(erwartet))
                self.app.aktion("mischen_beenden")
                self.app.aktualisieren(20)
                self.assertEqual(self.app.runde, runde + 1)
                self.assertEqual(self.app.phase, "uebergabe")
                self.assertEqual(kartenstand(self.app.spiel), kartenstand(erwartet))

    def test_spieleingaben_waehrend_mischen_gesperrt(self):
        self.app.aktion("starten")
        for aktion in ("starten", "bereit", "ziehen", "passen", "pause", "hilfe", "neustart"):
            self.app.aktion(aktion)
        self.app.aktion("mischen", 3)
        self.app.aktion("anzahl", 10)
        self.app.behandle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(self.app.phase, "mischen")
        self.assertEqual(self.app.spiel.spieler, ())
        self.assertEqual(self.app.mischanimation.verfahren, "zufall")
        self.assertEqual(self.app.mischanimation.spieleranzahl, 4)

    def test_tastatur_ueberspringt_und_neue_runde_animiert_erneut(self):
        for taste in (pygame.K_RETURN, pygame.K_SPACE):
            self.app.aktion("starten")
            self.app.behandle(pygame.event.Event(pygame.KEYDOWN, key=taste))
            self.assertEqual(self.app.phase, "uebergabe")
            self.app.phase = "ergebnis"
        self.app.aktion("starten")
        self.assertEqual(self.app.phase, "mischen")
        self.assertEqual(self.app.mischanimation.fortschritt(self.app.zeit), 0)

    def test_alle_animationen_rendern_ohne_handkarten_und_mit_skip_button(self):
        bilder = []
        for index in range(len(MISCHVERFAHREN)):
            self.app.phase = "start"
            self.app.aktion("mischen", index)
            self.app.aktion("starten")
            animation = self.app.mischanimation
            for fortschritt in (0, 0.1, 0.3, 0.5, 0.75, 0.9, 1):
                self.app.zeit = animation.beginn + animation.dauer * fortschritt
                bild = self.app.ansicht.zeichnen(self.app)
                self.assertEqual(self.app.ansicht.karten, [])
                self.assertEqual(
                    [button.aktion for button in self.app.ansicht.buttons], ["mischen_beenden"]
                )
                if fortschritt == 0.5:
                    bilder.append(pygame.image.tobytes(bild, "RGB"))
        self.assertEqual(len(set(bilder)), len(MISCHVERFAHREN))


if __name__ == "__main__":
    unittest.main()
