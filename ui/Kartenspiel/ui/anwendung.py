from dataclasses import dataclass

import pygame

from ..spiel import Spiel
from ..stapel import MISCHVERFAHREN
from .ansicht import GROESSE, Ansicht
from .assets import dateiname


@dataclass
class Animation:
    name: str
    von: pygame.Vector2
    nach: pygame.Vector2
    beginn: float
    dauer: float = 0.38


class Anwendung:
    def __init__(self, spiel: Spiel | None = None) -> None:
        pygame.display.init()
        pygame.font.init()
        self.fenster = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        pygame.display.set_caption("UNO")
        self.ansicht = Ansicht()
        pygame.display.set_icon(self.ansicht.assets.bild("Wild.png", 32, 46))
        self.spiel = spiel if spiel is not None else Spiel()
        self.phase = "start"
        self.vor_pause = "spielen"
        self.anzahl = 4
        self.mischindex = 0
        self.runde = 0
        self.zeit = 0.0
        self.laeuft = True
        self.maus = (-1, -1)
        self.hover: int | None = None
        self.gezogen_index: int | None = None
        self.klick_index: int | None = None
        self.klick_position = (0, 0)
        self.joker_index: int | None = None
        self.hand_start = 0
        self.animation: Animation | None = None
        self.spieler_vor_zug = 1
        self.meldung = ""
        self.meldung_bis = 0.0
        self.viewport = pygame.Rect(0, 0, 1280, 800)

    def laufen(self) -> None:
        uhr = pygame.time.Clock()
        try:
            while self.laeuft:
                self.aktualisieren(uhr.tick(60) / 1000)
                for event in pygame.event.get():
                    self.behandle(event)
                self.zeichnen()
        finally:
            pygame.quit()

    def aktualisieren(self, sekunden: float) -> None:
        self.zeit += sekunden
        if self.animation is not None and self.zeit >= self.animation.beginn + self.animation.dauer:
            self.animation = None
            self._nach_zug()

    def zeichnen(self) -> None:
        bild = self.ansicht.zeichnen(self)
        breite, hoehe = self.fenster.get_size()
        faktor = min(breite / GROESSE[0], hoehe / GROESSE[1])
        ziel = (max(1, round(GROESSE[0] * faktor)), max(1, round(GROESSE[1] * faktor)))
        self.viewport = pygame.Rect(0, 0, *ziel)
        self.viewport.center = (breite // 2, hoehe // 2)
        self.fenster.fill((8, 18, 14))
        self.fenster.blit(pygame.transform.smoothscale(bild, ziel), self.viewport)
        pygame.display.flip()

    def _position(self, position) -> tuple[int, int]:
        return (
            round((position[0] - self.viewport.x) * GROESSE[0] / self.viewport.width),
            round((position[1] - self.viewport.y) * GROESSE[1] / self.viewport.height),
        )

    def behandle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.laeuft = False
        elif event.type == pygame.KEYDOWN:
            self._taste(event.key)
        elif event.type == pygame.MOUSEWHEEL and self.phase == "spielen":
            self._blaettern(-event.y)
        elif event.type == pygame.WINDOWFOCUSLOST:
            if self.phase in ("spielen", "farbe", "uebergabe"):
                self._pause("pause")
        elif event.type == pygame.MOUSEMOTION:
            self.maus = self._position(event.pos)
            if self.klick_index is not None:
                if pygame.Vector2(self.maus).distance_to(self.klick_position) > 8:
                    self.gezogen_index = self.klick_index
            if self.phase == "spielen" and self.gezogen_index is None:
                karte = next(
                    (karte for karte in reversed(self.ansicht.karten) if karte.enthaelt(self.maus)),
                    None,
                )
                self.hover = karte.index if karte else None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.maus = self._position(event.pos)
            if self.phase == "spielen":
                for karte in reversed(self.ansicht.karten):
                    if karte.enthaelt(self.maus):
                        self.klick_index = karte.index
                        self.klick_position = self.maus
                        return
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.maus = self._position(event.pos)
            if self.klick_index is not None:
                index = self.klick_index
                ablegen = self.gezogen_index is None or pygame.Rect(
                    706, 288, 226, 259
                ).collidepoint(self.maus)
                self.klick_index = None
                self.gezogen_index = None
                if ablegen and self.phase == "spielen":
                    self.aktion("legen", index)
                return
            for button in reversed(self.ansicht.buttons):
                if button.rect.collidepoint(self.maus):
                    self.aktion(button.aktion, button.wert)
                    return

    def _taste(self, taste: int) -> None:
        if taste == pygame.K_ESCAPE:
            if self.phase in ("pause", "hilfe"):
                self.aktion("fortsetzen")
            elif self.phase == "farbe":
                self.aktion("abbrechen")
            elif self.phase == "start":
                self.laeuft = False
            elif self.phase != "animation":
                self._pause("pause")
        elif taste in (pygame.K_RETURN, pygame.K_SPACE):
            if self.phase == "uebergabe":
                self.aktion("bereit")
            elif self.phase == "start":
                self.aktion("starten")
        elif self.phase == "spielen":
            if taste == pygame.K_d:
                self.aktion("ziehen")
            elif taste == pygame.K_p and self.spiel.wartet_auf_gezogene_karte:
                self.aktion("passen")
            elif taste in (pygame.K_LEFT, pygame.K_RIGHT):
                self._blaettern(-1 if taste == pygame.K_LEFT else 1)

    def aktion(self, aktion: str, wert: int | str | None = None) -> None:
        try:
            self._aktion(aktion, wert)
        except ValueError as fehler:
            self._melden(str(fehler))

    def _aktion(self, aktion, wert):
        if aktion == "anzahl" and self.phase == "start":
            self.anzahl = wert
        elif aktion == "mischen" and self.phase == "start":
            self.mischindex = wert
        elif aktion == "starten" and self.phase in ("start", "ergebnis"):
            self.spiel.starten(self.anzahl, MISCHVERFAHREN[self.mischindex])
            self.runde += 1
            self.phase = "uebergabe"
            self.meldung = ""
            self.hand_start = 0
            self.hover = None
        elif aktion == "bereit" and self.phase == "uebergabe":
            self.phase = "spielen"
        elif aktion == "legen" and self.phase == "spielen":
            if wert not in self.spiel.legbare_indizes:
                self._melden("Diese Karte passt nicht. Wähle eine markierte Karte oder ziehe.")
                return
            karte = self.spiel.aktueller_spieler.getKarten()[wert]
            if karte.getFarbe() == "schwarz":
                self.joker_index = wert
                self.phase = "farbe"
            else:
                self._legen(wert)
        elif aktion == "farbe" and self.phase == "farbe":
            self._legen(self.joker_index, wert)
            self.joker_index = None
        elif aktion == "abbrechen" and self.phase == "farbe":
            self.joker_index = None
            self.phase = "spielen"
        elif aktion == "ziehen" and self.phase == "spielen":
            self.spieler_vor_zug = self.spiel.aktueller_spieler.getNummer()
            karte = self.spiel.ziehen()
            if karte is None:
                self._melden("Der Nachziehstapel ist leer. Der Zug geht weiter.")
                self._nach_zug()
            else:
                self._animieren("Deck.png", (600, 404), (720, 754))
                if self.spiel.wartet_auf_gezogene_karte:
                    self.hand_start = max(0, len(self.spiel.aktueller_spieler) - 12)
                    self._melden("Die gezogene Karte passt. Lege sie oder behalte sie.")
        elif aktion == "passen" and self.phase == "spielen":
            self.spieler_vor_zug = self.spiel.aktueller_spieler.getNummer()
            self.spiel.passen()
            self._nach_zug()
        elif aktion == "blaettern" and self.phase == "spielen":
            self._blaettern(wert)
        elif aktion in ("pause", "hilfe") and self.phase not in ("start", "animation"):
            self._pause(aktion)
        elif aktion == "fortsetzen" and self.phase in ("pause", "hilfe"):
            self.phase = self.vor_pause
        elif aktion == "neustart" and self.phase in ("pause", "ergebnis"):
            self.phase = "start"
            self.joker_index = None
            self.meldung = ""
        elif aktion == "beenden" and self.phase == "pause":
            self.laeuft = False

    def _legen(self, index: int, farbe: str | None = None) -> None:
        hand = self.spiel.aktueller_spieler
        self.spieler_vor_zug = hand.getNummer()
        vorher = {h.getNummer(): len(h) for h in self.spiel.spieler}
        position = next(
            (karte.rect.center for karte in self.ansicht.karten if karte.index == index),
            (720, 754),
        )
        karte = self.spiel.legen(index, farbe)
        meldungen = []
        for andere in self.spiel.spieler:
            differenz = len(andere) - vorher[andere.getNummer()]
            if differenz > 0:
                meldungen.append(f"Spieler {andere.getNummer()} zieht {differenz} und setzt aus.")
        if len(hand) == 1:
            meldungen.append(f"UNO! Spieler {hand.getNummer()} hat nur noch eine Karte.")
        if not hand:
            platz = self.spiel.platzierungen.index(hand.getNummer()) + 1
            meldungen.append(f"Spieler {hand.getNummer()} belegt Platz {platz}.")
        if meldungen:
            self._melden("  ·  ".join(meldungen))
        self._animieren(dateiname(karte), position, (819, 404))

    def _animieren(self, name, von, nach):
        self.animation = Animation(name, pygame.Vector2(von), pygame.Vector2(nach), self.zeit)
        self.phase = "animation"
        self.hover = None

    def _nach_zug(self):
        self.hover = None
        if self.spiel.beendet:
            self.phase = "ergebnis"
        elif self.spiel.aktueller_spieler.getNummer() != self.spieler_vor_zug:
            self.phase = "uebergabe"
            self.hand_start = 0
        else:
            self.phase = "spielen"
            self.hand_start = min(self.hand_start, max(0, len(self.spiel.aktueller_spieler) - 12))

    def _pause(self, phase):
        if self.phase in ("pause", "hilfe"):
            return
        self.vor_pause = self.phase
        self.phase = phase
        self.klick_index = None
        self.gezogen_index = None
        self.hover = None

    def _blaettern(self, richtung):
        maximum = max(0, len(self.spiel.aktueller_spieler) - 12)
        self.hand_start = max(0, min(maximum, self.hand_start + richtung * 6))
        self.hover = None
        self.klick_index = None
        self.gezogen_index = None

    def _melden(self, text):
        self.meldung = text
        self.meldung_bis = self.zeit + 5
