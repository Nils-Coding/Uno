from .karte import Karte


class Sonderkarte(Karte):
    def __init__(self, farbe: str, wert: str | None, funktion: str) -> None:
        super().__init__(farbe, wert)
        self.__funktion = funktion

    def get_Funktion(self) -> str:
        return self.__funktion

    def passt_auf(self, karte: Karte, farbe: str) -> bool:
        return (
            self.getFarbe() == "schwarz"
            or self.getFarbe() == farbe
            or (
                isinstance(karte, Sonderkarte)
                and self.__funktion == karte.get_Funktion()
                and self.getWert() == karte.getWert()
            )
        )

    def toString(self) -> str:
        teile = (self.getFarbe(), self.getWert(), self.__funktion)
        return " ".join(teil for teil in teile if teil is not None)
