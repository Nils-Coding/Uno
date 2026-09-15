from random import Random

from .hand import Hand
from .karte import Karte
from .sonderkarte import Sonderkarte
from .stapel import MISCHVERFAHREN, Stapel


class Spiel:
    def __init__(self, zufall: Random | None = None) -> None:
        self.__zufall = zufall
        self.__stapel = Stapel(zufall)
        self.__spieler: list[Hand] = []
        self.__am_zug = 0
        self.__richtung = 1
        self.__platzierungen: list[int] = []
        self.__gezogen: Karte | None = None
        self.__leerzuege = 0

    @property
    def stapel(self) -> Stapel:
        return self.__stapel

    @property
    def spieler(self) -> tuple[Hand, ...]:
        return tuple(self.__spieler)

    @property
    def aktueller_spieler(self) -> Hand:
        self._pruefe_laufend()
        return self.__spieler[self.__am_zug]

    @property
    def richtung(self) -> int:
        return self.__richtung

    @property
    def platzierungen(self) -> tuple[int, ...]:
        return tuple(self.__platzierungen)

    @property
    def wartet_auf_gezogene_karte(self) -> bool:
        return self.__gezogen is not None

    @property
    def festgefahren(self) -> bool:
        aktive = len(self.__spieler) - len(self.__platzierungen)
        return aktive > 1 and self.__leerzuege >= aktive

    @property
    def beendet(self) -> bool:
        return bool(self.__spieler) and (
            len(self.__platzierungen) == len(self.__spieler) or self.festgefahren
        )

    @property
    def legbare_indizes(self) -> tuple[int, ...]:
        hand = self.aktueller_spieler.getKarten()
        return tuple(
            index
            for index, karte in enumerate(hand)
            if (self.__gezogen is None or karte is self.__gezogen)
            and karte.passt_auf(self.__stapel.aufgedeckt(), self.__stapel.aktive_farbe)
            and not (
                karte.getFarbe() == "schwarz"
                and karte.getWert() == "4"
                and any(andere.getFarbe() == self.__stapel.aktive_farbe for andere in hand)
            )
        )

    def starten(self, spieleranzahl: int, mischverfahren: str = "zufall") -> None:
        if not 2 <= spieleranzahl <= 10:
            raise ValueError("Es müssen 2 bis 10 Spieler teilnehmen.")
        if mischverfahren not in MISCHVERFAHREN:
            raise ValueError("Unbekanntes Mischverfahren.")
        stapel = Stapel(self.__zufall)
        stapel.mischen(0, mischverfahren)
        spieler = stapel.ausgeben(spieleranzahl)
        self.__stapel = stapel
        self.__spieler = spieler
        self.__am_zug = 0
        self.__richtung = 1
        self.__platzierungen = []
        self.__gezogen = None
        self.__leerzuege = 0

    def legen(self, index: int, farbe: str | None = None) -> Karte:
        hand = self.aktueller_spieler
        if index not in self.legbare_indizes:
            raise ValueError("Diese Karte darf nicht gelegt werden.")
        karte = hand.getKarten()[index]
        if not hand.ablegen(self.__stapel, index, farbe):
            raise ValueError("Für einen Joker muss eine gültige Farbe gewählt werden.")
        self.__gezogen = None
        self.__leerzuege = 0
        aktive = len(self.__spieler) - len(self.__platzierungen)
        if not hand:
            self.__platzierungen.append(hand.getNummer())
        schritte = 1
        if isinstance(karte, Sonderkarte):
            funktion = karte.get_Funktion()
            if funktion == "Richtungswechsel":
                self.__richtung *= -1
                schritte = 2 if aktive == 2 else 1
            elif funktion == "Aussetzen":
                schritte = 2
            elif funktion == "ziehen":
                nachbar = self.__spieler[self._naechster(self.__am_zug)]
                for _ in range(int(karte.getWert())):
                    nachbar.ziehen(self.__stapel)
                schritte = 2
        verbleibend = [
            hand for hand in self.__spieler if hand.getNummer() not in self.__platzierungen
        ]
        if len(verbleibend) == 1:
            self.__platzierungen.append(verbleibend[0].getNummer())
        else:
            self._weiter(schritte)
        return karte

    def ziehen(self) -> Karte | None:
        hand = self.aktueller_spieler
        if self.__gezogen is not None:
            raise ValueError("Die gezogene Karte legen oder passen.")
        karte = hand.ziehen(self.__stapel)
        self.__gezogen = karte
        self.__leerzuege = self.__leerzuege + 1 if karte is None else 0
        if karte is None or not self.legbare_indizes:
            self._weiter()
        return karte

    def passen(self) -> None:
        self._pruefe_laufend()
        if self.__gezogen is None:
            raise ValueError("Vor dem Passen muss eine Karte gezogen werden.")
        self._weiter()

    def spielen(self) -> None:
        from .terminal import Terminal

        Terminal().spielen(self)

    def _pruefe_laufend(self) -> None:
        if not self.__spieler:
            raise ValueError("Das Spiel wurde noch nicht gestartet.")
        if self.beendet:
            raise ValueError("Die Runde ist beendet.")

    def _naechster(self, index: int) -> int:
        while True:
            index = (index + self.__richtung) % len(self.__spieler)
            if self.__spieler[index].getNummer() not in self.__platzierungen:
                return index

    def _weiter(self, schritte: int = 1) -> None:
        self.__gezogen = None
        for _ in range(schritte):
            self.__am_zug = self._naechster(self.__am_zug)
