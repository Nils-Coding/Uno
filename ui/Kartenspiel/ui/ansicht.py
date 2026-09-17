from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from .assets import Assets, dateiname
from .effekte import impuls, konfetti, pokal, tischlicht

if TYPE_CHECKING:
    from .anwendung import Anwendung

GROESSE = (1440, 900)
HELL = (244, 242, 228)
LEISE = (155, 179, 167)
AKZENT = (208, 239, 151)
PANEL = (18, 39, 33)
RAND = (49, 75, 63)
FARBEN = {
    "blau": (25, 161, 211),
    "rot": (239, 62, 79),
    "grün": (69, 174, 103),
    "gelb": (249, 200, 57),
}


@dataclass
class Schaltflaeche:
    rect: pygame.Rect
    aktion: str
    wert: int | str | None = None


@dataclass
class Kartenflaeche:
    index: int
    rect: pygame.Rect
    bild: pygame.Surface

    def enthaelt(self, position: tuple[int, int]) -> bool:
        if not self.rect.collidepoint(position):
            return False
        x, y = position[0] - self.rect.x, position[1] - self.rect.y
        return self.bild.get_at((x, y)).a > 100


class Ansicht:
    def __init__(self) -> None:
        self.flaeche = pygame.Surface(GROESSE)
        self.assets = Assets()
        self.buttons: list[Schaltflaeche] = []
        self.karten: list[Kartenflaeche] = []
        self.maus = (-1, -1)
        self._kartenhub = {}
        self.hintergrund = self.assets.bild("Table_3.png", *GROESSE).copy()
        self.hintergrund.fill((95, 135, 109), special_flags=pygame.BLEND_RGB_MULT)
        self.schrift = pygame.font.match_font("Arial,DejaVu Sans")
        self.fette_schrift = pygame.font.match_font("Arial,DejaVu Sans", bold=True)
        self.font = lru_cache(maxsize=32)(self.font)

    def font(self, groesse: int, fett: bool = False) -> pygame.font.Font:
        return pygame.font.Font(self.fette_schrift if fett else self.schrift, groesse)

    def text(self, text, position, groesse=20, farbe=HELL, fett=False, mitte=False):
        bild = self.font(groesse, fett).render(str(text), True, farbe)
        rect = bild.get_rect(center=position) if mitte else bild.get_rect(topleft=position)
        self.flaeche.blit(bild, rect)

    def panel(self, rect, farbe=PANEL, radius=20):
        pygame.draw.rect(self.flaeche, farbe, rect, border_radius=radius)
        pygame.draw.rect(self.flaeche, RAND, rect, width=1, border_radius=radius)

    def button(self, rect, label, aktion, wert=None, aktiv=False, an=True):
        rect = pygame.Rect(rect)
        hover = an and rect.collidepoint(self.maus)
        farbe = AKZENT if aktiv else ((43, 67, 54) if hover else PANEL)
        if aktiv and hover:
            farbe = (224, 250, 185)
        self.panel(rect, farbe, 12)
        self.text(label, rect.center, 17, PANEL if aktiv else (HELL if an else LEISE), True, True)
        if an:
            self.buttons.append(Schaltflaeche(rect, aktion, wert))

    def karte(self, name, mitte, hoehe=190, winkel=0, markiert=False):
        bild = self.assets.karte(name, hoehe, winkel, markiert)
        rect = bild.get_rect(center=mitte)
        self.flaeche.blit(bild, rect)
        return bild, rect

    def zeichnen(self, app: Anwendung) -> pygame.Surface:
        self.buttons = []
        self.karten = []
        self.maus = app.maus
        self.flaeche.blit(self.hintergrund, (0, 0))
        self._kopf(app)
        if app.phase == "start":
            self._start(app)
        elif app.phase == "mischen":
            self._mischen(app)
        else:
            self._tisch(app)
            if app.phase == "animation":
                self._spieleffekt(app)
            if app.phase in ("uebergabe", "farbe", "ergebnis", "pause", "hilfe"):
                self._dialog(app)
        if app.animation is not None and app.zeit < app.animation.beginn + app.animation.dauer:
            animation = app.animation
            t = min(1, (app.zeit - animation.beginn) / animation.dauer)
            weich = 1 - (1 - t) ** 3
            position = animation.von.lerp(animation.nach, weich)
            position.y -= math.sin(t * math.pi) * 38
            self.karte(animation.name, position, round(190 + math.sin(t * math.pi) * 18), (1 - weich) * -12)
        if app.phase not in ("start", "mischen", "pause", "hilfe", "ergebnis", "uebergabe"):
            impuls(self.flaeche, app.zeit - app.impuls_seit, FARBEN.get(app.impuls_farbe, AKZENT))
        if app.gezogen_index is not None and app.phase == "spielen":
            karte = app.spiel.aktueller_spieler.getKarten()[app.gezogen_index]
            self.karte(dateiname(karte), app.maus, 208, -4, True)
        effekt_sichtbar = (app.effekt and app.phase == "animation"
                          and 0 <= app.zeit - app.effekt.beginn < app.effekt.dauer)
        if app.meldung and app.zeit < app.meldung_bis and app.phase != "ergebnis" and not effekt_sichtbar:
            breite = min(1220, self.font(18).size(app.meldung)[0] + 56)
            self.panel((720 - breite // 2, 92, breite, 48), (36, 57, 42), 24)
            self.text(app.meldung, (720, 116), 18, AKZENT, mitte=True)
        if app.ton.stumm:
            self.text("TON AUS · M", (875, 39), 13, LEISE, True)
        return self.flaeche

    def _kopf(self, app):
        if app.phase != "start":
            self.text("UNO", (48, 22), 35, HELL, True)
        for index, farbe in enumerate(FARBEN.values()):
            x = 48 if app.phase == "start" else 147
            pygame.draw.circle(self.flaeche, farbe, (x + index * 12, 46), 4)
        pygame.draw.line(self.flaeche, RAND, (48, 80), (1392, 80))
        if app.phase != "start":
            runde = app.runde + 1 if app.phase == "mischen" else app.runde
            self.text(f"RUNDE {runde:02}", (1060, 39), 14, LEISE, True)
            if app.phase != "mischen":
                self.button((1200, 25, 88, 40), "Regeln", "hilfe")
                self.button((1300, 25, 92, 40), "Pause", "pause")

    def _mischen(self, app):
        animation = app.mischanimation
        t = animation.fortschritt(app.zeit)
        self.text("DIE RUNDE WIRD VORBEREITET", (720, 146), 13, AKZENT, True, True)
        self.text(f"Wir mischen: {animation.titel}", (720, 200), 43, HELL, True, True)
        self.text(animation.beschreibung, (720, 248), 19, LEISE, mitte=True)
        pygame.draw.ellipse(self.flaeche, RAND, (245, 308, 950, 320), 1)
        for x, y, winkel in animation.karten(app.zeit):
            self.karte("Deck.png", (round(x), round(y)), 128, round(winkel))
        self.text(animation.schritt(app.zeit), (720, 666), 21, HELL, True, True)
        pygame.draw.rect(self.flaeche, RAND, (500, 705, 440, 5), border_radius=2)
        if t > 0:
            pygame.draw.rect(self.flaeche, AKZENT, (500, 705, max(1, round(440 * t)), 5), border_radius=2)
        self.text(
            f"Anschließend erhält jeder der {animation.spieleranzahl} Spieler 7 Karten.",
            (720, 744), 16, LEISE, mitte=True,
        )
        self.button((595, 797, 250, 49), "Überspringen  →", "mischen_beenden")
        self.text("Enter oder Leertaste zum Überspringen", (720, 869), 12, LEISE, mitte=True)

    def _start(self, app):
        self.text("DER SPIELEABEND BEGINNT HIER", (88, 245), 13, AKZENT, True)
        self.text("UNO", (82, 264), 156, HELL, True)
        self.text("Ein Tisch. Alle gegen alle.", (88, 453), 26, HELL)
        self.text("2–10 Spieler · Gemeinsam an einem Bildschirm", (88, 496), 17, LEISE)
        for name, x, y, winkel in (
            ("Blue_2.png", 907, 357, 23),
            ("Green_Reverse.png", 1040, 325, 6),
            ("Red_7.png", 1173, 365, -15),
        ):
            self.karte(name, (x, y + math.sin(app.zeit * 1.4 + x) * 5), 295, winkel)
        self.panel((64, 625, 1312, 158), (15, 34, 29), 24)
        self.text("Spieler", (92, 652), 21, HELL, True)
        for nummer in range(2, 11):
            self.button(
                (92 + (nummer - 2) * 47, 695, 40, 45),
                str(nummer),
                "anzahl",
                nummer,
                app.anzahl == nummer,
            )
        self.text("Mischverfahren", (564, 652), 21, HELL, True)
        for index, name in enumerate(("Zufall", "Overhand", "Riffle", "Häufchen")):
            self.button(
                (564 + index * 127, 695, 118, 45),
                name,
                "mischen",
                index,
                app.mischindex == index,
            )
        self.button((1112, 674, 230, 65), "Spiel starten", "starten", aktiv=True)
        self.panel((64, 800, 1312, 76), (15, 34, 29), 20)
        self.text("KLANG", (88, 829), 13, AKZENT, True)
        self._tonschalter(app, 164, 817)
        self._lautstaerke(app, "Effekte", "effektpegel", app.ton.effekte, 410, 817)
        self.button((757, 817, 160, 42), "Musik an" if app.ton.musik_an else "Musik aus",
                    "musik", aktiv=app.ton.musik_an, an=app.ton.verfuegbar)
        self._lautstaerke(app, "Musik", "musikpegel", app.ton.musik, 965, 817)

    def _tonschalter(self, app, x, y):
        label = "Ton aus · M" if app.ton.stumm else "Ton an · M"
        if not app.ton.verfuegbar:
            label = "Kein Audiogerät"
        self.button((x, y, 188, 42), label, "stumm",
                    aktiv=not app.ton.stumm and app.ton.verfuegbar, an=app.ton.verfuegbar)

    def _lautstaerke(self, app, label, aktion, wert, x, y):
        self.text(label, (x, y + 11), 16, LEISE)
        self.button((x + 76, y, 40, 42), "−", aktion, -10,
                    an=app.ton.verfuegbar and wert > 0)
        self.text(f"{round(wert * 100)} %", (x + 157, y + 21), 17, HELL, True, True)
        self.button((x + 198, y, 40, 42), "+", aktion, 10,
                    an=app.ton.verfuegbar and wert < 1)

    def _tisch(self, app):
        spiel = app.spiel
        aktive_farbe = FARBEN.get(spiel.stapel.aktive_farbe, AKZENT)
        self.flaeche.blit(tischlicht(aktive_farbe), (559, 219))
        pygame.draw.ellipse(self.flaeche, (59, 88, 68), (220, 215, 1000, 338), 1)
        pygame.draw.ellipse(self.flaeche, (37, 66, 51), (230, 225, 980, 318), 1)
        self._mitspieler(app)
        self.text("DER TISCH", (720, 255), 12, LEISE, True, True)
        if app.phase in ("spielen", "animation"):
            self._verlauf(app)
        startwinkel = math.pi / 5 if spiel.richtung == 1 else math.pi * 4 / 5
        pygame.draw.arc(self.flaeche, LEISE, (706, 288, 28, 28), startwinkel, startwinkel + 5, 2)
        pfeil = [(732, 288), (735, 298), (724, 295)]
        if spiel.richtung == -1:
            pfeil = [(1440 - x, y) for x, y in pfeil]
        pygame.draw.polygon(self.flaeche, LEISE, pfeil)
        for index in range(min(4, spiel.stapel.getAnzahl())):
            self.karte("Deck.png", (600 - index * 2, 410 - index * 2), 174)
        if not spiel.stapel.getAnzahl():
            self.panel((533, 319, 132, 180))
            self.text("Neu mischen", (599, 408), 16, LEISE, mitte=True)
        if app.phase == "spielen" and not spiel.wartet_auf_gezogene_karte:
            self.buttons.append(Schaltflaeche(pygame.Rect(519, 311, 160, 202), "ziehen"))
        abgelegt = spiel.stapel.getAbgelegt()
        if app.animation and app.animation.name != "Deck.png" and app.zeit < app.animation.beginn + app.animation.dauer:
            abgelegt = abgelegt[:-1]
        if app.gezogen_index is not None:
            erlaubt = app.gezogen_index in spiel.legbare_indizes
            ziel_farbe = AKZENT if erlaubt else FARBEN["rot"]
            pygame.draw.rect(self.flaeche, ziel_farbe, (738, 290, 162, 230), 2, border_radius=20)
            self.text("Hier ablegen" if erlaubt else "Passt nicht", (819, 278), 15, ziel_farbe, True, True)
        for index, karte in enumerate(abgelegt[-3:]):
            self.karte(dateiname(karte), (819, 404), 185, (len(abgelegt[-3:]) - 1 - index) * 7 - 5)
        self.text("NACHZIEHEN", (599, 526), 12, LEISE, True, True)
        self.text(f"{spiel.stapel.getAnzahl()} Karten", (599, 551), 15, HELL, mitte=True)
        self.text("ABLAGE", (819, 526), 12, LEISE, True, True)
        farbe = spiel.stapel.aktive_farbe
        pygame.draw.circle(self.flaeche, FARBEN.get(farbe, HELL), (783, 552), 5)
        self.text(farbe.capitalize(), (801, 540), 16)
        if not spiel.beendet:
            self.text("GLEICH AM ZUG" if app.phase == "animation" else "DU BIST DRAN",
                      (1102, 331), 12, AKZENT, True)
            self.text(f"Spieler {spiel.aktueller_spieler.getNummer()}", (1098, 354), 30, HELL, True)
            if app.phase == "spielen":
                erlaubt = len(spiel.legbare_indizes)
                hinweis = f"{erlaubt} passende Karte" + ("n" if erlaubt != 1 else "")
                self.text(hinweis if erlaubt else "Zeit für eine neue Karte.", (1102, 399), 16, LEISE)
            warten = spiel.wartet_auf_gezogene_karte
            self.button(
                (1102, 446, 251, 52),
                "Karte behalten  →" if warten else "+  Karte ziehen",
                "passen" if warten else "ziehen",
                aktiv=True,
                an=app.phase == "spielen",
            )
        self.panel((24, 601, 1392, 274), (14, 32, 27), 24)
        if app.phase in ("spielen", "farbe"):
            self._hand(app)
        else:
            for index in range(7):
                self.karte("Deck.png", (504 + index * 72, 753), 159, 9 - index * 3)
        self.text("Klicken oder auf die Ablage ziehen", (48, 882), 12, LEISE)
        self.text("D  Ziehen   ·   ← →  Hand blättern   ·   Esc  Pause", (1040, 882), 12, LEISE)

    def _verlauf(self, app):
        effekt = app.effekt
        if effekt and app.phase == "animation" and 0 <= app.zeit - effekt.beginn < effekt.dauer:
            return
        self.text("LETZTE AKTIONEN", (70, 323), 11, LEISE, True)
        if not app.verlauf:
            self.text("Der erste Zug gehört dir.", (70, 358), 17, HELL)
        for i, (spieler, text, farbe) in enumerate(reversed(app.verlauf)):
            y = 357 + i * 61
            pygame.draw.circle(self.flaeche, FARBEN.get(farbe, AKZENT), (76, y + 7), 3)
            self.text(spieler, (91, y - 3), 13, HELL if i == 0 else LEISE, True)
            while self.font(14).size(text)[0] > 260:
                text = text[:-2].rstrip("…") + "…"
            self.text(text, (91, y + 18), 14, LEISE)

    def _spieleffekt(self, app):
        effekt = app.effekt
        if not effekt or not 0 <= app.zeit - effekt.beginn < effekt.dauer:
            return
        t = app.zeit - effekt.beginn
        farbe = FARBEN.get(effekt.farbe, AKZENT)
        y = 345 + round(16 * (1 - min(1, t / 0.18)) ** 3)
        self.panel((48, y - 31, 355, 177), (19, 43, 35), 22)
        pygame.draw.rect(self.flaeche, farbe, (70, y - 9, 37, 4), border_radius=2)
        groesse = 52 if len(effekt.titel) < 7 else 27
        self.text(effekt.titel, (70, y + 16), groesse, HELL, True)
        # Lange Hinweise bleiben auch bei zweistelligen Spielernummern im Panel.
        woerter = effekt.detail.split()
        zeile, zeilen = "", []
        for wort in woerter:
            kandidat = f"{zeile} {wort}".strip()
            if self.font(15).size(kandidat)[0] > 305:
                zeilen.append(zeile)
                zeile = wort
            else:
                zeile = kandidat
        zeilen.append(zeile)
        for i, zeile in enumerate(zeilen):
            self.text(zeile, (70, y + 90 + i * 20), 15, LEISE)

    def _mitspieler(self, app):
        spiel = app.spiel
        nummer = spiel.aktueller_spieler.getNummer() if not spiel.beendet else None
        andere = [hand for hand in spiel.spieler if hand.getNummer() != nummer]
        breite = min(190, 1296 // max(1, len(andere)))
        start = 720 - len(andere) * breite / 2
        for index, hand in enumerate(andere):
            x = int(start + index * breite + breite / 2)
            fertig = hand.getNummer() in spiel.platzierungen
            for k in range(min(5, len(hand))):
                self.karte("Deck.png", (x - 22 + k * 11, 155), 67, 8 - k * 4)
            if fertig:
                platz = spiel.platzierungen.index(hand.getNummer()) + 1
                self.text(f"{platz}. PLATZ", (x, 152), 17, AKZENT, True, True)
            self.text(f"Spieler {hand.getNummer()}", (x, 212), 15, HELL, True, True)
            self.text(
                "UNO!" if len(hand) == 1 else f"{len(hand)} Karten", (x, 235), 12, LEISE, mitte=True
            )

    def _hand(self, app):
        spiel = app.spiel
        hand = spiel.aktueller_spieler
        karten = hand.getKarten()
        erlaubt = spiel.legbare_indizes
        self.text(f"Spieler {hand.getNummer()}", (49, 617), 20, HELL, True)
        self.text(f"{len(karten)} KARTEN", (1270, 623), 12, LEISE, True)
        if len(karten) == 1:
            self.panel((225, 611, 77, 32), FARBEN["rot"], 10)
            self.text("UNO!", (263, 627), 15, HELL, True, True)
        ende = min(len(karten), app.hand_start + 12)
        anzahl = ende - app.hand_start
        schritt = min(96, 1070 / max(1, anzahl - 1))
        reihenfolge = []
        for stelle, index in enumerate(range(app.hand_start, ende)):
            t = (stelle - (anzahl - 1) / 2) / max(1, (anzahl - 1) / 2)
            x = 720 + (stelle - (anzahl - 1) / 2) * schritt
            ziel = 30 if app.hover == index else 0
            hub = self._kartenhub.get(index, 0)
            hub += (ziel - hub) * min(1, app.delta * 16)
            self._kartenhub[index] = hub
            aufdecken = max(0, min(1, (app.zeit - app.hand_seit - stelle * 0.018) / 0.32))
            y = 757 + abs(t) * 15 - hub + 30 * (1 - aufdecken) ** 3
            winkel = round(-t * 10, 1)
            bild = self.assets.karte(dateiname(karten[index]), 180, winkel, index in erlaubt)
            if index not in erlaubt:
                bild = bild.copy()
                bild.fill((158, 171, 162, 255), special_flags=pygame.BLEND_RGB_MULT)
            reihenfolge.append(Kartenflaeche(index, bild.get_rect(center=(x, y)), bild))
        reihenfolge.sort(key=lambda karte: karte.index == app.hover)
        for karte in reihenfolge:
            if karte.index != app.gezogen_index:
                self.flaeche.blit(karte.bild, karte.rect)
                self.karten.append(karte)
        if len(karten) > 12:
            self.button((41, 736, 43, 46), "‹", "blaettern", -1, an=app.hand_start > 0)
            self.button((1356, 736, 43, 46), "›", "blaettern", 1, an=ende < len(karten))
            self.text(
                f"{app.hand_start + 1}–{ende} / {len(karten)}", (720, 853), 11, LEISE, mitte=True
            )
        if app.hover is not None and app.hover < len(karten):
            self.text(str(karten[app.hover]), (720, 581), 16, HELL, mitte=True)

    def _dialog(self, app):
        dunkel = pygame.Surface(GROESSE, pygame.SRCALPHA)
        dunkel.fill((4, 13, 10, 228))
        self.flaeche.blit(dunkel, (0, 0))
        self.buttons = []
        self.karten = []
        if app.phase == "ergebnis":
            self._ergebnis(app)
            return
        self.panel((395, 169, 650, 592) if app.phase == "pause" else (395, 219, 650, 460),
                   (19, 41, 33), 28)
        if app.phase == "uebergabe":
            nummer = app.spiel.aktueller_spieler.getNummer()
            pygame.draw.circle(self.flaeche, RAND, (720, 306), 49)
            pygame.draw.circle(self.flaeche, AKZENT, (720, 306), 49, 2)
            self.text(f"{nummer:02}", (720, 306), 34, HELL, True, True)
            self.text("DEIN ZUG", (720, 385), 12, AKZENT, True, True)
            self.text(
                f"Spieler {nummer}",
                (720, 427),
                48,
                HELL,
                True,
                True,
            )
            self.text("Bildschirm weitergeben. Deine Hand bleibt verdeckt.",
                      (720, 493), 17, LEISE, mitte=True)
            self.button((493, 553, 454, 60), "Hand aufdecken  →", "bereit", aktiv=True)
            self.text("Enter oder Leertaste", (720, 642), 13, LEISE, mitte=True)
        elif app.phase == "farbe":
            self.text("Farbe wählen", (720, 323), 43, HELL, True, True)
            for index, (name, farbe) in enumerate(FARBEN.items()):
                rect = pygame.Rect(438 + index * 145, 421, 129, 112)
                self.panel(rect, farbe, 18)
                self.text(name.capitalize(), rect.center, 20, (11, 30, 25), True, True)
                if rect.collidepoint(app.maus):
                    pygame.draw.rect(self.flaeche, HELL, rect, 3, border_radius=18)
                self.buttons.append(Schaltflaeche(rect, "farbe", name))
            self.button((590, 583, 260, 48), "Zurück zur Hand", "abbrechen")
        elif app.phase == "pause":
            self.text("Pause", (720, 244), 43, HELL, True, True)
            self.button((493, 318, 454, 57), "Weiterspielen", "fortsetzen", aktiv=True)
            self._tonschalter(app, 493, 409)
            self.button((759, 409, 188, 42), "Musik an" if app.ton.musik_an else "Musik aus",
                        "musik", aktiv=app.ton.musik_an, an=app.ton.verfuegbar)
            self._lautstaerke(app, "Effekte", "effektpegel", app.ton.effekte, 493, 468)
            self._lautstaerke(app, "Musik", "musikpegel", app.ton.musik, 493, 523)
            self.button((493, 616, 220, 51), "Neue Runde", "neustart")
            self.button((728, 616, 219, 51), "Beenden", "beenden")
            self.text("Neue Runde beendet die laufende Runde.", (720, 704), 14, LEISE, mitte=True)
        else:
            self.text("Spielregeln", (720, 311), 35, HELL, True, True)
            zeilen = (
                "Lege die gleiche Farbe, Zahl oder das gleiche Symbol.",
                "Helle Ränder zeigen dir, welche Karten passen.",
                "Ziehe freiwillig; nur die neue Karte darf dann gelegt werden.",
                "+2 / +4: Der Nächste zieht und setzt aus. Kein Stapeln.",
                "+4 geht nur ohne die aktive Farbe. Joker wählen eine Farbe.",
                "UNO und die Platzierungen werden automatisch angezeigt.",
                "Die vier optionalen Spezialjoker sind normale Farbwahljoker.",
            )
            for index, zeile in enumerate(zeilen):
                self.text(zeile, (425, 361 + index * 31), 16, LEISE)
            self.button((493, 601, 454, 49), "Alles klar", "fortsetzen", aktiv=True)

    def _ergebnis(self, app):
        spiel = app.spiel
        gold = (239, 203, 117)
        self.panel((400, 105, 640, 735), (19, 41, 33), 28)
        self.text(f"RUNDE {app.runde:02} · BEENDET", (720, 143), 13, AKZENT, True, True)
        if not spiel.festgefahren:
            pokal(self.flaeche, (720, 215), gold)
        else:
            self.karte("Deck.png", (720, 219), 92, -8)
        titel = (
            "Runde beendet" if spiel.festgefahren else f"Spieler {spiel.platzierungen[0]} gewinnt!"
        )
        self.text(titel, (720, 304), 36, HELL, True, True)
        sekunden = int(app.spielzeit)
        untertitel = ("Keine weiteren Züge möglich." if spiel.festgefahren else
                      f"{app.aktionen} Aktionen  ·  {sekunden // 60}:{sekunden % 60:02} Minuten am Tisch")
        self.text(untertitel, (720, 345), 16, LEISE, mitte=True)
        self.text("PLATZIERUNG", (454, 381), 10, LEISE, True)
        self.text("SIEGE IN DIESER SERIE", (848, 381), 10, LEISE, True)
        for index, nummer in enumerate(spiel.platzierungen):
            y = 407 + index * 28
            if index == 0 and not spiel.festgefahren:
                pygame.draw.rect(self.flaeche, (42, 58, 39), (443, y - 4, 554, 27), border_radius=8)
            self.text(f"{index + 1:02}", (463, y), 16, gold if index == 0 else LEISE, True)
            self.text(f"Spieler {nummer}", (518, y), 16, HELL, True)
            self.text(str(app.siege.get(nummer, 0)), (930, y), 16, gold, True)
        self.button((456, 723, 312, 56), "Revanche  →", "starten", aktiv=True)
        self.button((785, 723, 200, 56), "Zum Start", "neustart")
        self.text("Gleiche Spieler, nächste Runde. Die Serie geht weiter.", (720, 808), 13, LEISE, mitte=True)
        if not spiel.festgefahren:
            konfetti(self.flaeche, app.zeit - app.ergebnis_seit, tuple(FARBEN.values()) + (gold,))
