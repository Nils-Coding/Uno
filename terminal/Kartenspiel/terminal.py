from .karte import FARBEN
from .spiel import Spiel
from .stapel import MISCHVERFAHREN


# Übernimmt die Eingaben und Ausgaben für das Terminal-Spiel.
class Terminal:
    def __init__(
        self,
        eingabe=input,
        ausgabe=print,
    ) -> None:
        self.eingabe = eingabe
        self.ausgabe = ausgabe

    # Fragt die Einstellungen ab und bietet nach jeder Runde eine weitere an.
    def spielen(self, spiel) -> None:
        self.ausgabe("UNO · 2–10 Spieler · q beendet das Spiel")
        try:
            anzahl = self._zahl("Anzahl der Spieler: ", 2, 10)
            self.ausgabe("Mischen: 0 Zufall · 1 Overhand · 2 Riffle · 3 Häufchen")
            verfahren = MISCHVERFAHREN[self._zahl("Mischverfahren [0–3]: ", 0, 3)]
            while True:
                spiel.starten(anzahl, verfahren)
                self._runde(spiel)
                if not self._ja_nein("Noch eine Runde? [j/n]: "):
                    break
        except (EOFError, KeyboardInterrupt):
            self.ausgabe("\nSpiel beendet.")

    # Führt die Spieler durch ihre Züge und zeigt am Ende die Platzierungen.
    def _runde(self, spiel) -> None:
        while not spiel.beendet:
            hand = spiel.aktueller_spieler
            self._lesen(f"\nSpieler {hand.getNummer()}: Enter, um die Hand anzuzeigen. ")
            self.ausgabe("\n" * 30)
            # Zeigt die aktuelle Ablage, die Kartenanzahlen und die eigene Hand.
            richtung = "im Uhrzeigersinn" if spiel.richtung == 1 else "gegen den Uhrzeigersinn"
            self.ausgabe(f"Aufgedeckt: {spiel.stapel.aufgedeckt()}")
            self.ausgabe(f"Aktive Farbe: {spiel.stapel.aktive_farbe} · {richtung}")
            self.ausgabe(
                "Karten: " + " · ".join(f"Spieler {h.getNummer()}: {len(h)}" for h in spiel.spieler)
            )
            self.ausgabe(str(hand))
            self.ausgabe(
                f"Legbare Indizes: {', '.join(map(str, spiel.legbare_indizes)) or 'keine'}"
            )
            # Fragt nach der Aktion und lässt eine Karte legen oder ziehen.
            if self._ja_nein("Möchtest du eine Karte legen? [j/n]: "):
                if not spiel.legbare_indizes:
                    self.ausgabe("Keine passende Karte. Du musst ziehen.")
                    self._ziehen(spiel)
                else:
                    self._legen(spiel)
            else:
                self._ziehen(spiel)
            # Meldet UNO und neu erreichte Platzierungen.
            if len(hand) == 1:
                self.ausgabe(f"Spieler {hand.getNummer()}: UNO!")
            if hand.getNummer() in spiel.platzierungen:
                platz = spiel.platzierungen.index(hand.getNummer()) + 1
                self.ausgabe(f"Spieler {hand.getNummer()} belegt Platz {platz}.")
            # Verdeckt die Hand durch Leerzeilen vor dem nächsten Spielerwechsel.
            self._lesen("Enter, um den Zug abzuschließen. ")
            self.ausgabe("\n" * 30)
        if spiel.festgefahren:
            self.ausgabe("Keine Karten mehr ziehbar; alle Spieler haben gepasst. Runde beendet.")
        self.ausgabe("Platzierungen:")
        for platz, nummer in enumerate(spiel.platzierungen, start=1):
            self.ausgabe(f"{platz}. Platz: Spieler {nummer}")

    # Fragt eine erlaubte Karte und bei Jokern die gewünschte Farbe ab.
    def _legen(self, spiel, index: int | None = None) -> None:
        while True:
            auswahl = index
            if auswahl is None:
                auswahl = self._zahl("Kartenindex: ", 0, len(spiel.aktueller_spieler) - 1)
            if auswahl not in spiel.legbare_indizes:
                self.ausgabe("Diese Karte passt nicht. Wähle einen legbaren Index.")
                continue
            karte = spiel.aktueller_spieler.getKarten()[auswahl]
            farbe = None
            if karte.getFarbe() == "schwarz":
                self.ausgabe("Farbe: 0 blau · 1 rot · 2 grün · 3 gelb")
                farbe = FARBEN[self._zahl("Gewünschte Farbe [0–3]: ", 0, 3)]
            spiel.legen(auswahl, farbe)
            self.ausgabe(f"Gelegt: {karte}")
            return

    # Zeigt die gezogene Karte und bietet bei passender Karte das Ablegen an.
    def _ziehen(self, spiel) -> None:
        karte = spiel.ziehen()
        self.ausgabe(f"Gezogen: {karte}" if karte is not None else "Keine Karte mehr ziehbar.")
        if spiel.wartet_auf_gezogene_karte:
            if self._ja_nein("Die gezogene Karte passt. Jetzt legen? [j/n]: "):
                self._legen(spiel, len(spiel.aktueller_spieler) - 1)
            else:
                spiel.passen()

    # Vereinheitlicht die Eingabe und beendet das Spiel bei q.
    def _lesen(self, frage: str) -> str:
        antwort = self.eingabe(frage).strip().lower()
        if antwort == "q":
            raise EOFError
        return antwort

    # Fragt so lange nach, bis eine ganze Zahl im erlaubten Bereich eingegeben wird.
    def _zahl(self, frage: str, minimum: int, maximum: int) -> int:
        while True:
            try:
                zahl = int(self._lesen(frage))
            except ValueError:
                self.ausgabe("Bitte eine ganze Zahl eingeben.")
                continue
            if minimum <= zahl <= maximum:
                return zahl
            self.ausgabe(f"Bitte eine Zahl zwischen {minimum} und {maximum} eingeben.")

    # Akzeptiert kurze und ausgeschriebene Ja-Nein-Antworten.
    def _ja_nein(self, frage: str) -> bool:
        while True:
            antwort = self._lesen(frage)
            if antwort in ("j", "ja", "n", "nein"):
                return antwort in ("j", "ja")
            self.ausgabe("Bitte j oder n eingeben.")


# Erstellt ein Spiel und startet die Terminal-Oberfläche.
def main() -> None:
    Spiel().spielen()
