from random import Random

from .hand import Hand
from .karte import FARBEN, Karte
from .sonderkarte import Sonderkarte

MISCHVERFAHREN = ("zufall", "overhand", "riffle", "häufchen")


# Verwaltet den Ziehstapel, den Ablagestapel und die aktive Farbe.
class Stapel:
    def __init__(self, zufall=None) -> None:
        self.__zufall = zufall if zufall is not None else Random()
        self.__verdeckt: list = []
        self.__abgelegt: list = []
        self.__farbe: str | None = None
        # Erstellt die Zahlenkarten und farbigen Sonderkarten.
        for farbe in FARBEN:
            self.__verdeckt.append(Karte(farbe, "0"))
            for _ in range(2):
                self.__verdeckt.extend(Karte(farbe, str(wert)) for wert in range(1, 10))
                self.__verdeckt.extend(
                    [
                        Sonderkarte(farbe, "2", "ziehen"),
                        Sonderkarte(farbe, None, "Aussetzen"),
                        Sonderkarte(farbe, None, "Richtungswechsel"),
                    ]
                )
        # Ergänzt die schwarzen Jokerkarten.
        for _ in range(4):
            self.__verdeckt.append(Sonderkarte("schwarz", None, "Joker"))
            self.__verdeckt.append(Sonderkarte("schwarz", "4", "ziehen"))
        self.__verdeckt.append(Sonderkarte("schwarz", None, "Handkarten-Misch-Joker"))
        self.__verdeckt.extend(
            Sonderkarte("schwarz", None, "Individueller Joker") for _ in range(3)
        )

    # Liefert auch die durch einen Joker gewählte Farbe.
    @property
    def aktive_farbe(self) -> str | None:
        return self.__farbe

    # Gibt Kopien der Stapel zurück, damit die Originale geschützt bleiben.
    def getVerdeckt(self) -> list:
        return self.__verdeckt.copy()

    def getAbgelegt(self) -> list:
        return self.__abgelegt.copy()

    def setVerdeckt(self, karten: list) -> None:
        self.__verdeckt = list(karten)

    # Deckt eine Karte auf oder ersetzt den Ablagestapel und aktualisiert die Farbe.
    def setAbgelegt(self, karten: list | None = None) -> list:
        if karten is None:
            karte = self.ziehen()
            if karte is None:
                raise ValueError("Keine Karte zum Aufdecken vorhanden.")
            self.__abgelegt.append(karte)
        else:
            self.__abgelegt = list(karten)
        self.__farbe = self.__abgelegt[-1].getFarbe() if self.__abgelegt else None
        return self.getAbgelegt()

    # Bereitet die beiden Stapel für eine Textausgabe auf.
    def verdecktToString(self) -> str:
        return "\n".join(["verdeckt:", *map(str, self.__verdeckt)])

    def abgelegtToString(self) -> str:
        return "\n".join(["abgelegt:", *map(str, self.__abgelegt)])

    # Mischt den Ziehstapel (0) oder den Ablagestapel mit dem gewählten Verfahren.
    def mischen(self, stapelnummer: int, verfahren: str = "zufall") -> None:
        if verfahren not in MISCHVERFAHREN:
            raise ValueError("Unbekanntes Mischverfahren.")
        karten = self.__verdeckt if stapelnummer == 0 else self.__abgelegt
        if verfahren == "zufall":
            self.__zufall.shuffle(karten)
        elif verfahren == "overhand":
            # Overhand: Verschiebt mehrfach kleine Kartenpakete.
            for _ in range(12):
                rest = karten.copy()
                karten.clear()
                while rest:
                    anzahl = self.__zufall.randint(1, min(8, len(rest)))
                    karten.extend(rest[-anzahl:])
                    del rest[-anzahl:]
        elif verfahren == "riffle":
            # Riffle: Teilt den Stapel und verzahnt die beiden Hälften.
            for _ in range(7):
                mitte = sum(self.__zufall.randrange(2) for _ in karten)
                links, rechts = karten[:mitte][::-1], karten[mitte:][::-1]
                karten.clear()
                while links or rechts:
                    stapel = (
                        links
                        if self.__zufall.randrange(len(links) + len(rechts)) < len(links)
                        else rechts
                    )
                    karten.append(stapel.pop())
        else:
            # Verteilt Karten auf sieben Häufchen und fügt diese wieder zusammen.
            haeufchen: list[list] = [[] for _ in range(7)]
            for karte in karten:
                self.__zufall.choice(haeufchen).append(karte)
            self.__zufall.shuffle(haeufchen)
            karten[:] = [karte for haufen in haeufchen for karte in haufen]
        if stapelnummer != 0 and karten:
            self.__farbe = karten[-1].getFarbe()

    # Liefert die oberste Karte des Ablagestapels.
    def aufgedeckt(self):
        if not self.__abgelegt:
            raise ValueError("Der Ablagestapel ist leer.")
        return self.__abgelegt[-1]

    def getAnzahl(self) -> int:
        return len(self.__verdeckt)

    # Gibt jedem Spieler sieben Karten und deckt eine Zahlenkarte als Start auf.
    def ausgeben(self, spieleranzahl: int) -> list:
        if not 2 <= spieleranzahl <= 10:
            raise ValueError("Es müssen 2 bis 10 Spieler teilnehmen.")
        if len(self.__verdeckt) < spieleranzahl * 7 + 1:
            raise ValueError("Nicht genügend Karten zum Austeilen.")
        if not any(type(karte) is Karte for karte in self.__verdeckt[: -spieleranzahl * 7]):
            raise ValueError("Keine Zahlenkarte als Startkarte vorhanden.")
        spieler = [Hand([], nummer) for nummer in range(1, spieleranzahl + 1)]
        for _ in range(7):
            for hand in spieler:
                hand.ziehen(self)
        self.setAbgelegt([])
        while isinstance(self.setAbgelegt()[-1], Sonderkarte):
            pass
        return spieler

    # Füllt einen leeren Ziehstapel aus der Ablage auf; die oberste Karte bleibt liegen.
    def ziehen(self):
        if not self.__verdeckt and len(self.__abgelegt) > 1:
            self.__verdeckt = self.__abgelegt[:-1]
            self.__abgelegt = self.__abgelegt[-1:]
            self.mischen(0)
        return self.__verdeckt.pop() if self.__verdeckt else None

    # Prüft die Karte und die Farbwahl, bevor sie auf den Ablagestapel kommt.
    def ablegen(self, karte, farbe: str | None = None) -> bool:
        if not self.__abgelegt or not karte.passt_auf(self.aufgedeckt(), self.__farbe):
            return False
        if karte.getFarbe() == "schwarz":
            if farbe not in FARBEN:
                return False
        elif farbe is not None:
            return False
        self.__abgelegt.append(karte)
        self.__farbe = farbe if karte.getFarbe() == "schwarz" else karte.getFarbe()
        return True
