import os
from pathlib import Path
from random import Random
import tempfile
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from Kartenspiel.karte import Karte
from Kartenspiel.sonderkarte import Sonderkarte
from Kartenspiel.spiel import Spiel
from Kartenspiel.ui.anwendung import Anwendung
from Kartenspiel.ui.audio import AUDIO, KLAENGE, Soundmanager


class AudioTest(unittest.TestCase):
    def setUp(self):
        self.ordner = tempfile.TemporaryDirectory()
        self.pfad = Path(self.ordner.name) / "audio.json"
        self.ton = Soundmanager(self.pfad)

    def tearDown(self):
        pygame.quit()
        self.ordner.cleanup()

    def app(self, anzahl=3):
        app = Anwendung(Spiel(Random(42)), ton=self.ton)
        app.aktion("anzahl", anzahl)
        app.aktion("starten")
        app.aktion("mischen_beenden")
        app.aktion("bereit")
        self.ton.stoppen()
        return app

    def hand(self, app, karten):
        app.spiel.aktueller_spieler.setKarten(karten)
        app.spiel.stapel.setAbgelegt([Karte("rot", "5")])

    def test_alle_sounds_und_musik_sind_vollstaendig_ladbar(self):
        self.assertTrue(self.ton.verfuegbar)
        for name, (dateien, _, _) in KLAENGE.items():
            self.assertEqual(len(self.ton._sounds[name]), len(dateien), name)
            for sound in self.ton._sounds[name]:
                self.assertGreater(sound.get_length(), 0)
        self.assertAlmostEqual(self.ton._musik.get_length(), 19.2, places=2)
        self.assertTrue((AUDIO / "LICENSE-casino.txt").is_file())

    def test_fehlendes_audiogeraet_verhindert_keinen_spielstart(self):
        pygame.mixer.quit()
        with patch("pygame.mixer.init", side_effect=pygame.error("Kein Gerät")):
            self.ton = Soundmanager(self.pfad)
        app = self.app()
        self.assertFalse(self.ton.verfuegbar)
        app.aktion("ziehen")
        app.aktualisieren(0.5)
        app.zeichnen()
        self.assertNotEqual(app.phase, "animation")

    def test_einstellungen_werden_gespeichert_und_begrenzt(self):
        self.ton.einstellen("effekte", 2)
        self.ton.einstellen("musik", -1)
        self.ton.einstellen("musik_an", True)
        self.ton.einstellen("stumm", True)
        geladen = Soundmanager(self.pfad)
        self.assertEqual((geladen.effekte, geladen.musik, geladen.musik_an, geladen.stumm),
                         (1, 0, True, True))
        self.pfad.write_text('{"effekte": "laut", "musik": null, "stumm": "ja"}')
        geladen = Soundmanager(self.pfad)
        self.assertEqual(geladen.effekte, 0.65)
        self.assertFalse(geladen.stumm)
        self.pfad.write_text("kaputt")
        self.assertFalse(Soundmanager(self.pfad).stumm)

    def test_unbeschreibbare_einstellungen_bleiben_in_der_sitzung_nutzbar(self):
        with patch.object(Path, "write_text", side_effect=OSError("schreibgeschützt")):
            self.ton.einstellen("effekte", 0.3)
        self.assertEqual(self.ton.effekte, 0.3)

    def test_stumm_stoppt_effekte_musik_und_geplante_folgen(self):
        self.ton.einstellen("musik_an", True)
        self.ton.aktualisieren(0.3)
        self.ton.spielen("legen", nach=0.2)
        self.ton.spielen("ziehen")
        self.ton.einstellen("stumm", True)
        self.assertFalse(self.ton._folge)
        self.assertEqual(self.ton._musikkanal.get_volume(), 0)
        self.assertTrue(all(not k.get_busy() for gruppe in self.ton._kanaele.values() for k in gruppe))
        self.ton.einstellen("stumm", False)
        self.ton.aktualisieren(0.3)
        self.assertNotIn("legen", self.ton._letzter_ton)

    def test_sperrzeit_und_varianten(self):
        self.ton.spielen("legen")
        erster = self.ton._letzte_datei["legen"]
        self.ton.spielen("legen")
        self.assertEqual(self.ton._letzte_datei["legen"], erster)
        self.ton.aktualisieren(0.1)
        self.ton.spielen("legen")
        self.assertNotEqual(self.ton._letzte_datei["legen"], erster)

    def test_fokusverlust_friert_animation_und_soundzeit_ein(self):
        app = self.app()
        app.aktion("ziehen")
        zeit = app.zeit
        tonzeit = self.ton.zeit
        app.behandle(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        app.aktualisieren(10)
        self.assertEqual((app.zeit, self.ton.zeit), (zeit, tonzeit))
        app.behandle(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        app.aktualisieren(0.4)
        self.assertIsNone(app.animation)

    def test_ueberspringen_entfernt_alle_mischgeraeusche(self):
        app = Anwendung(ton=self.ton)
        app.aktion("starten")
        self.assertTrue(self.ton._folge)
        app.aktion("mischen_beenden")
        self.assertEqual([name for _, _, name in self.ton._folge], ["bereit"])
        app.aktualisieren(0.2)
        self.assertFalse(self.ton._folge)

    def test_spielerwechsel_und_hand_aufdecken_bleiben_still(self):
        app = self.app()
        self.hand(app, [Karte("rot", "7"), Karte("blau", "1"), Karte("grün", "2")])
        app.aktion("legen", 0)
        app.aktualisieren(0.56)
        self.assertEqual(app.phase, "uebergabe")
        self.ton.stoppen()
        with patch.object(self.ton, "spielen", wraps=self.ton.spielen) as spielen:
            app.aktion("bereit")
            app.aktualisieren(0.1)
        self.assertEqual(app.phase, "spielen")
        spielen.assert_not_called()

    def test_karte_erklingt_erst_bei_der_landung_und_uno_danach(self):
        app = self.app()
        self.hand(app, [Karte("rot", "7"), Karte("blau", "1")])
        app.aktion("legen", 0)
        self.assertNotIn("legen", self.ton._letzter_ton)
        app.aktualisieren(0.30)
        self.assertNotIn("legen", self.ton._letzter_ton)
        app.aktualisieren(0.09)
        self.assertIn("legen", self.ton._letzter_ton)
        app.aktualisieren(0.12)
        self.assertIn("uno", self.ton._letzter_ton)

    def test_sonderkarten_haben_eigene_signale_und_richtige_ziehfolge(self):
        for karte, signal, anzahl in (
            (Sonderkarte("rot", None, "Aussetzen"), "aussetzen", 0),
            (Sonderkarte("rot", None, "Richtungswechsel"), "richtung", 0),
            (Sonderkarte("rot", "2", "ziehen"), "strafe", 2),
            (Sonderkarte("schwarz", "4", "ziehen"), "strafe", 4),
            (Sonderkarte("schwarz", None, "Joker"), "joker", 0),
        ):
            with self.subTest(karte=str(karte)):
                app = self.app()
                self.hand(app, [karte, Karte("blau", "1"), Karte("grün", "3")])
                app.aktion("legen", 0)
                if app.phase == "farbe":
                    app.aktion("farbe", "gelb")
                namen = [name for _, _, name in self.ton._folge]
                self.assertIn(signal, namen)
                self.assertEqual(namen.count("ziehen"), anzahl)

    def test_ungueltiger_zug_spielt_nur_fehler(self):
        app = self.app()
        self.hand(app, [Karte("blau", "1"), Karte("grün", "3")])
        app.aktion("legen", 0)
        self.assertEqual(app.phase, "spielen")
        self.assertEqual(set(self.ton._letzter_ton), {"fehler"})
        self.assertFalse(self.ton._folge)

    def test_letzte_karte_spielt_rundensieg_statt_uno(self):
        app = self.app(2)
        self.hand(app, [Karte("rot", "7")])
        app.aktion("legen", 0)
        namen = [name for _, _, name in self.ton._folge]
        self.assertIn("sieg", namen)
        self.assertNotIn("uno", namen)
        app.aktualisieren(0.39)
        self.assertEqual(app.phase, "ergebnis")
        app.aktualisieren(0.12)
        self.assertIn("sieg", self.ton._letzter_ton)

    def test_musik_ist_optional_und_von_effekten_unabhaengig(self):
        self.ton.aktualisieren(0.5)
        self.assertFalse(self.ton._musikkanal.get_busy())
        self.ton.einstellen("effekte", 0)
        self.ton.einstellen("musik_an", True)
        self.ton.aktualisieren(0.5)
        self.assertTrue(self.ton._musikkanal.get_busy())
        laut = self.ton._musikkanal.get_volume()
        self.ton.aktualisieren(0.5, leise=True)
        self.assertLess(self.ton._musikkanal.get_volume(), laut)

    def test_kein_nachholen_alter_sounds_nach_haenger(self):
        self.ton.spielen("ziehen", nach=0.1)
        self.ton.spielen("legen", nach=0.3)
        self.ton.aktualisieren(5)
        self.assertFalse(self.ton._letzter_ton)
        self.assertFalse(self.ton._folge)


if __name__ == "__main__":
    unittest.main()
