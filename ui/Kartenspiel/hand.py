from __future__ import annotations

from typing import TYPE_CHECKING

from .karte import Karte

if TYPE_CHECKING:
    from .stapel import Stapel


class Hand:
    def __init__(self, karten: list[Karte], nummer: int) -> None:
        self.setKarten(karten)
        self.setNummer(nummer)

    def getKarten(self) -> list[Karte]:
        return self.__karten.copy()

    def setKarten(self, karten: list[Karte]) -> None:
        self.__karten = list(karten)

    def getNummer(self) -> int:
        return self.__nummer

    def setNummer(self, nummer: int) -> None:
        if nummer < 1:
            raise ValueError("Spielernummern beginnen bei 1.")
        self.__nummer = nummer

    def ziehen(self, stapel: Stapel) -> Karte | None:
        karte = stapel.ziehen()
        if karte is not None:
            self.__karten.append(karte)
        return karte

    def ablegen(self, stapel: Stapel, index: int, farbe: str | None = None) -> bool:
        if not 0 <= index < len(self.__karten):
            return False
        if not stapel.ablegen(self.__karten[index], farbe):
            return False
        self.__karten.pop(index)
        return True

    def toString(self) -> str:
        zeilen = [f"Spieler {self.__nummer}"]
        zeilen.extend(f"{index}: {karte}" for index, karte in enumerate(self.__karten))
        return "\n".join(zeilen)

    def __str__(self) -> str:
        return self.toString()

    def __len__(self) -> int:
        return len(self.__karten)
