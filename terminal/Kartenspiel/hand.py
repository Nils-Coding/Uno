# Verwaltet die Karten und die Nummer eines Spielers.
class Hand:
    def __init__(self, karten: list, nummer: int) -> None:
        self.setKarten(karten)
        self.setNummer(nummer)

    # Gibt eine Kopie zurück, damit die Hand nicht von außen verändert wird.
    def getKarten(self) -> list:
        return self.__karten.copy()

    def setKarten(self, karten: list) -> None:
        self.__karten = list(karten)

    def getNummer(self) -> int:
        return self.__nummer

    def setNummer(self, nummer: int) -> None:
        if nummer < 1:
            raise ValueError("Spielernummern beginnen bei 1.")
        self.__nummer = nummer

    # Nimmt eine Karte vom Stapel auf die Hand.
    def ziehen(self, stapel):
        karte = stapel.ziehen()
        if karte is not None:
            self.__karten.append(karte)
        return karte

    # Entfernt eine Karte erst nach erfolgreichem Ablegen aus der Hand.
    def ablegen(self, stapel, index: int, farbe: str | None = None) -> bool:
        if not 0 <= index < len(self.__karten):
            return False
        if not stapel.ablegen(self.__karten[index], farbe):
            return False
        self.__karten.pop(index)
        return True

    # Listet die Handkarten mit ihren auswählbaren Indizes auf.
    def toString(self) -> str:
        zeilen = [f"Spieler {self.__nummer}"]
        zeilen.extend(f"{index}: {karte}" for index, karte in enumerate(self.__karten))
        return "\n".join(zeilen)

    # Ermöglicht die Textausgabe der Hand mit str() und print().
    def __str__(self) -> str:
        return self.toString()

    # Liefert die Kartenanzahl für len() und Prüfungen auf eine leere Hand.
    def __len__(self) -> int:
        return len(self.__karten)
