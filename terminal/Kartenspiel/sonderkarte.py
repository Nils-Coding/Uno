from .karte import Karte

# Erweitert eine Karte um eine Sonderfunktion wie Aussetzen oder Ziehen.
class Sonderkarte(Karte):
    def __init__(self, farbe: str, wert: str | None, funktion: str) -> None:
        super().__init__(farbe, wert)
        self.__funktion = funktion

    def get_Funktion(self) -> str:
        return self.__funktion

    # Erlaubt Joker sowie passende Farben oder gleiche Sonderfunktionen und Werte.
    def passt_auf(self, karte, farbe: str) -> bool:
        return (
            self.getFarbe() == "schwarz"
            or self.getFarbe() == farbe
            or (
                isinstance(karte, Sonderkarte)
                and self.__funktion == karte.get_Funktion()
                and self.getWert() == karte.getWert()
            )
        )

    # Erstellt den Kartentext und lässt fehlende Werte weg.
    def toString(self) -> str:
        teile = (self.getFarbe(), self.getWert(), self.__funktion)
        return " ".join(teil for teil in teile if teil is not None)
