"""Zeitbasierte Darstellung der Mischverfahren mit verdeckten Beispielkarten."""

import math
from dataclasses import dataclass


def _weich(wert: float) -> float:
    t = max(0.0, min(1.0, wert))
    return t * t * (3 - 2 * t)


def _weg(von, nach, fortschritt, bogen=0):
    t = _weich(fortschritt)
    return (
        von[0] + (nach[0] - von[0]) * t,
        von[1] + (nach[1] - von[1]) * t - math.sin(t * math.pi) * bogen,
        von[2] + (nach[2] - von[2]) * t,
    )


def _stapel(index, x=720, y=450):
    return x + index * 0.65, y - index * 0.8, 0


@dataclass
class Mischanimation:
    verfahren: str
    beginn: float
    spieleranzahl: int
    dauer: float = 5.4

    @property
    def titel(self) -> str:
        return {
            "zufall": "Zufall",
            "overhand": "Overhand",
            "riffle": "Riffle",
            "häufchen": "Häufchen",
        }[self.verfahren]

    @property
    def beschreibung(self) -> str:
        return {
            "zufall": "Die Karten werden zufällig neu angeordnet.",
            "overhand": "Kleine Kartenpäckchen wandern auf einen neuen Stapel.",
            "riffle": "Zwei Stapelhälften werden ineinander verzahnt.",
            "häufchen": "Die Karten werden auf sieben Häufchen verteilt und eingesammelt.",
        }[self.verfahren]

    def fortschritt(self, zeit: float) -> float:
        return max(0.0, min(1.0, (zeit - self.beginn) / self.dauer))

    def schritt(self, zeit: float) -> str:
        t = self.fortschritt(zeit)
        if t >= 0.85:
            return "Stapel zusammenlegen"
        return {
            "zufall": "Karten auffächern" if t < 0.2 else "Karten durchmischen",
            "overhand": "Stapel aufnehmen" if t < 0.15 else "Päckchen abziehen",
            "riffle": "Stapel teilen" if t < 0.23 else "Karten ineinander mischen",
            "häufchen": "Karten verteilen" if t < 0.7 else "Häufchen einsammeln",
        }[self.verfahren]

    def karten(self, zeit: float) -> list[tuple[float, float, float]]:
        """Position und Winkel von 28 Beispielkarten, von hinten nach vorne.

        Die Darstellung nutzt keinen Zufallsgenerator des Spiels. Die tatsächliche
        Kartenreihenfolge bestimmt weiterhin Stapel.mischen beim Rundenstart.
        """
        t = self.fortschritt(zeit)
        karten = []
        for index in range(28):
            if self.verfahren == "zufall":
                position, ebene = self._zufall(index, t)
            elif self.verfahren == "overhand":
                position, ebene = self._overhand(index, t)
            elif self.verfahren == "riffle":
                position, ebene = self._riffle(index, t)
            else:
                position, ebene = self._haeufchen(index, t)
            karten.append((ebene, position))
        return [position for _, position in sorted(karten, key=lambda karte: karte[0])]

    def _zufall(self, index, t):
        winkel = index * 2.39996
        radius = 85 + (index % 5) * 36

        def verteilt(drehung):
            richtung = 1 if index % 2 else -1
            phase = winkel + drehung * richtung * (1 + index % 3 * 0.35)
            return (
                720 + math.cos(phase) * radius * 1.65,
                465 + math.sin(phase) * radius * 0.42,
                math.sin(phase) * 65,
            )

        if t < 0.2:
            return _weg(_stapel(index), verteilt(0), t / 0.2), index
        if t < 0.72:
            return verteilt(_weich((t - 0.2) / 0.52) * math.tau), index
        return _weg(verteilt(math.tau), _stapel(index), (t - 0.72) / 0.28), index

    def _overhand(self, index, t):
        quelle = _stapel(index, 850, 395)
        paket = (27 - index) // 4
        zielindex = paket * 4 + index % 4
        ziel = _stapel(zielindex, 585, 490)
        if t < 0.15:
            return _weg(_stapel(index), quelle, t / 0.15), index
        if t < 0.85:
            zug = (t - 0.15) / 0.7 * 7 - paket
            ebene = 100 + index if 0 < zug < 1 else (zielindex if zug >= 1 else index)
            return _weg(quelle, ziel, zug, 75), ebene
        return _weg(ziel, _stapel(zielindex), (t - 0.85) / 0.15), zielindex

    def _riffle(self, index, t):
        seite = index // 14
        reihe = index % 14
        quelle = (535 + seite * 370 + reihe * 0.65, 420 - reihe * 0.8, 12 - seite * 24)
        zielindex = reihe * 2 + seite
        ziel = _stapel(zielindex, 720, 490)
        if t < 0.23:
            return _weg(_stapel(index), quelle, t / 0.23), index
        if t < 0.85:
            zug = (t - 0.23) / 0.62 * 30 - zielindex
            ebene = 100 + zielindex if 0 < zug < 3 else (zielindex if zug >= 3 else index)
            return _weg(quelle, ziel, zug / 3, 40), ebene
        return _weg(ziel, _stapel(zielindex), (t - 0.85) / 0.15), zielindex

    def _haeufchen(self, index, t):
        zugnummer = 27 - index
        # Sichtbar unregelmäßig verteilen, jedes Häufchen erhält vier Karten.
        haufen = (3, 0, 5, 2, 6, 1, 4)[zugnummer % 7]
        hoehe = zugnummer // 7
        quelle = _stapel(index, 720, 365)
        ziel = _stapel(hoehe, 360 + haufen * 120, 490)
        if t < 0.08:
            return _weg(_stapel(index), quelle, t / 0.08), index
        if t < 0.7:
            zug = (t - 0.08) / 0.62 * 30 - zugnummer
            ebene = 100 + index if 0 < zug < 3 else (hoehe if zug >= 3 else index)
            return _weg(quelle, ziel, zug / 3, 30), ebene
        reihenfolge = (2, 5, 0, 6, 3, 1, 4).index(haufen)
        zielindex = reihenfolge * 4 + hoehe
        zug = (t - 0.7) / 0.3 * 8 - reihenfolge
        return _weg(ziel, _stapel(zielindex), zug / 2, 35), 100 + zielindex if 0 < zug < 2 else zielindex
