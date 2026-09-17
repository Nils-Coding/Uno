"""Vorgeladene Klänge, zeitgesteuerte Folgen und getrennte Musiklautstärke."""

import heapq
import json
from pathlib import Path
from random import Random
import sys

import pygame


AUDIO = Path(__file__).with_name("assets") / "audio"
# Dateien, Pegel, Kanalgruppe. Musikalische Motive teilen dieselbe Klangfarbe.
KLAENGE = {
    "klick": (("click_001.ogg", "click_002.ogg"), 0.42, "ui"),
    "auf": (("open_001.ogg",), 0.22, "ui"),
    "zu": (("close_001.ogg",), 0.22, "ui"),
    "zurueck": (("back_001.ogg",), 0.38, "ui"),
    "farbe": (("confirmation_001.ogg",), 0.20, "ui"),
    "fehler": (("error_001.ogg",), 0.30, "ui"),
    "mischen": (("card-shuffle.ogg",), 0.48, "karten"),
    "ziehen": (tuple(f"card-slide-{i}.ogg" for i in range(1, 5)), 0.62, "karten"),
    "legen": (tuple(f"card-place-{i}.ogg" for i in range(1, 5)), 0.70, "karten"),
    **{name: ((f"{name}.wav",), pegel, "motiv") for name, pegel in (
        ("bereit", 0.42), ("joker", 0.60), ("uno", 0.80), ("richtung", 0.58),
        ("aussetzen", 0.58), ("strafe", 0.55), ("fertig", 0.70),
        ("sieg", 0.85), ("ende", 0.55),
    )},
}


class Soundmanager:
    def __init__(self, einstellungen: Path | None = None):
        self.einstellungen = einstellungen or self._einstellungspfad()
        self.effekte = 0.65
        self.musik = 0.25
        self.musik_an = False
        self.stumm = False
        self.verfuegbar = False
        self.pausiert = False
        self.zeit = 0.0
        self._folge = []
        self._nummer = 0
        self._letzter_ton = {}
        self._letzte_datei = {}
        self._zufall = Random()  # Niemals den Zufallsgenerator des Spiels verwenden.
        self._sounds = {}
        self._kanaele = {}
        self._musik = None
        self._musikpegel = 0.0
        self._laden()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)
            self._kanaele = {"ui": [pygame.mixer.Channel(0)],
                             "karten": [pygame.mixer.Channel(i) for i in (1, 2, 3)],
                             "motiv": [pygame.mixer.Channel(i) for i in (4, 5)]}
            self._musikkanal = pygame.mixer.Channel(6)
            for name, (dateien, pegel, _) in KLAENGE.items():
                self._sounds[name] = []
                for datei in dateien:
                    try:
                        sound = pygame.mixer.Sound(AUDIO / datei)
                        sound.set_volume(pegel)
                        self._sounds[name].append(sound)
                    except (pygame.error, OSError):
                        continue
            try:
                self._musik = pygame.mixer.Sound(AUDIO / "tischmusik.wav")
            except (pygame.error, OSError):
                pass
            self.verfuegbar = True
            self._pegel_setzen()
        except pygame.error:
            # Audio ist optional: Ohne Gerät bleiben alle Spielaktionen verfügbar.
            pass

    @staticmethod
    def _einstellungspfad():
        basis = Path.home() / ("Library/Application Support" if sys.platform == "darwin" else ".config")
        return basis / "uno-kartenspiel" / "audio.json"

    def _laden(self):
        try:
            daten = json.loads(self.einstellungen.read_text())
            if not isinstance(daten, dict):
                return
            for name in ("effekte", "musik"):
                wert = daten.get(name)
                if type(wert) in (int, float) and 0 <= wert <= 1:
                    setattr(self, name, float(wert))
            for name in ("musik_an", "stumm"):
                if isinstance(daten.get(name), bool):
                    setattr(self, name, daten[name])
        except (OSError, ValueError):
            pass

    def einstellen(self, name, wert):
        if name in ("effekte", "musik"):
            setattr(self, name, round(max(0.0, min(1.0, wert)), 2))
        elif name in ("stumm", "musik_an"):
            setattr(self, name, bool(wert))
        else:
            raise ValueError("Unbekannte Toneinstellung")
        if self.stumm or self.effekte == 0:
            self.stoppen()
        self._pegel_setzen()
        try:
            self.einstellungen.parent.mkdir(parents=True, exist_ok=True)
            self.einstellungen.write_text(json.dumps({name: getattr(self, name) for name in
                ("effekte", "musik", "musik_an", "stumm")}, indent=2) + "\n")
        except OSError:
            pass

    def _pegel_setzen(self):
        if not self.verfuegbar:
            return
        for kanaele in self._kanaele.values():
            for kanal in kanaele:
                kanal.set_volume(0 if self.stumm else self.effekte)
        if self.stumm:
            self._musikpegel = 0
            self._musikkanal.set_volume(0)

    def spielen(self, name, nach=0.0):
        if not self.verfuegbar or self.stumm or self.pausiert or self.effekte == 0:
            return
        if nach > 0:
            self._nummer += 1
            heapq.heappush(self._folge, (self.zeit + nach, self._nummer, name))
            return
        sounds = self._sounds.get(name, [])
        sperre = 0.28 if name == "fehler" else 0.065
        if not sounds or self.zeit - self._letzter_ton.get(name, -10) < sperre:
            return
        auswahl = [i for i in range(len(sounds)) if i != self._letzte_datei.get(name)]
        index = self._zufall.choice(auswahl or [0])
        kanaele = self._kanaele[KLAENGE[name][2]]
        kanal = next((k for k in kanaele if not k.get_busy()), kanaele[0])
        kanal.play(sounds[index])
        self._letzter_ton[name] = self.zeit
        self._letzte_datei[name] = index

    def aktualisieren(self, sekunden, leise=False):
        if self.pausiert or not self.verfuegbar:
            return
        self.zeit += sekunden
        while self._folge and self._folge[0][0] <= self.zeit:
            zeit, _, name = heapq.heappop(self._folge)
            if self.zeit - zeit <= 0.25:  # Nach einem Hänger keine Klanglawine nachholen.
                self.spielen(name)
        ziel = self.musik * 0.5 * (0.35 if leise else 1) if self.musik_an and not self.stumm else 0
        if self._musik and ziel > 0 and not self._musikkanal.get_busy():
            self._musikkanal.set_volume(0)
            self._musikkanal.play(self._musik, loops=-1)
        self._musikpegel += (ziel - self._musikpegel) * min(1, sekunden * 4)
        self._musikkanal.set_volume(self._musikpegel)
        if ziel == 0 and self._musikpegel < 0.001:
            self._musikkanal.stop()

    def stoppen(self):
        """Szenenwechsel verwirft auch noch ausstehende Effekte."""
        self._folge.clear()
        self._letzter_ton.clear()
        for kanaele in self._kanaele.values():
            for kanal in kanaele:
                kanal.stop()

    def fokus(self, aktiv):
        self.pausiert = not aktiv
        if self.verfuegbar:
            if aktiv:
                pygame.mixer.unpause()
            else:
                pygame.mixer.pause()

    def schliessen(self):
        self.stoppen()
        if self.verfuegbar:
            self._musikkanal.stop()

    def mischfolge(self, animation):
        """Geräusche folgen den Bewegungsphasen der vier Mischverfahren."""
        self.stoppen()
        self.spielen("ziehen")
        dauer = animation.dauer
        if animation.verfahren == "overhand":
            for i in range(7):
                self.spielen("ziehen", nach=dauer * (0.15 + (i + 0.6) * 0.7 / 7))
        elif animation.verfahren == "häufchen":
            for i in range(28):
                self.spielen("legen", nach=dauer * (0.08 + (i + 2) * 0.62 / 30))
            for i in range(7):
                self.spielen("ziehen", nach=dauer * (0.7 + (i + 1) * 0.3 / 8))
        else:
            beginn = 0.23 if animation.verfahren == "riffle" else 0.2
            # Die Aufnahme enthält bereits eine vollständige dreisekündige Folge.
            self.spielen("mischen", nach=dauer * beginn)
        self.spielen("legen", nach=dauer * 0.97)
