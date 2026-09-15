FARBEN = ("blau", "rot", "grün", "gelb")


class Karte:
    def __init__(self, farbe: str, wert: str | None) -> None:
        self.setFarbe(farbe)
        self.setWert(wert)

    def getFarbe(self) -> str:
        return self.__farbe

    def getWert(self) -> str | None:
        return self.__wert

    def setFarbe(self, farbe: str) -> None:
        if farbe not in (*FARBEN, "schwarz"):
            raise ValueError("Unbekannte Kartenfarbe.")
        self.__farbe = farbe

    def setWert(self, wert: str | None) -> None:
        self.__wert = wert

    def passt_auf(self, karte: "Karte", farbe: str) -> bool:
        return self.getFarbe() == farbe or (
            type(self) is type(karte) and self.getWert() == karte.getWert()
        )

    def toString(self) -> str:
        return f"{self.__farbe} {self.__wert}"

    def __str__(self) -> str:
        return self.toString()


if __name__ == "__main__":
    print(Karte("blau", "0"))
    print(Karte("rot", "6"))
