# Soundauswahl für UNO (ursprüngliche Vorauswahl)

**Umgesetzt:** Die endgültigen Karten- und UI-Geräusche liegen jetzt unter
`Kartenspiel/ui/assets/audio/` und sind ins Spiel eingebunden. Musikalische
Akzente und der optionale Hintergrundloop wurden passend dazu prozedural
erzeugt (`tools/klangwelt_erzeugen.py`). Die Kenney-Pizzicato-Jingles bleiben
hier als Alternativen zum Vergleichen. Bedienung und aktueller Stand stehen
in der [Projekt-README](../README.md). Der folgende Text dokumentiert die
ursprüngliche Vorauswahl und Planung.

Heruntergeladene Vorauswahl vom 17. September 2026: 42 OGG-Dateien,
zusammen rund 0,5 MB. Alle Dateien wurden mit dem vorhandenen pygame-Mixer
erfolgreich geladen. Die Auswahl ist noch nicht ins Spiel eingebunden und
noch nicht nach Gehör abschließend abgestimmt.

## Klangrichtung

Ein gemütlicher Kartentisch mit etwas spielerischem Charakter: echte
Kartengeräusche als Grundlage, zurückhaltende UI-Klicks und kurze musikalische
Akzente. Häufige Aktionen bleiben leise; UNO und Rundenende dürfen auffallen.

## Quellen und Lizenzen

Alle drei Pakete stammen von Kenney und sind als CC0 veröffentlicht.
Die jeweilige unveränderte `License.txt` liegt im Unterordner.

| Ordner | Originalpaket | Vorauswahl |
| --- | --- | --- |
| `casino/` | [Casino Audio](https://kenney.nl/assets/casino-audio) | 11 Karten-, Fächer- und Mischgeräusche |
| `interface/` | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | 14 Klicks, Bestätigungs- und Dialogsignale |
| `jingles/` | [Music Jingles](https://kenney.nl/assets/music-jingles) | 17 kurze Pizzicato-Varianten zum Vergleichen |

## Geplante Zuordnung

Die Dateinamen sind Kandidaten. Besonders die musikalischen Signale müssen
noch angehört und auf ihre Wirkung im Spiel geprüft werden.

| Spielereignis | Kandidaten / Umsetzung |
| --- | --- |
| Spielerzahl oder Mischverfahren wählen | `interface/click_001.ogg`, alternativ `click_002.ogg` |
| Dialog öffnen / schließen | `interface/open_001.ogg`, `close_001.ogg` |
| Farbwahl bestätigen | `interface/confirmation_001.ogg` |
| Zurück / Farbwahl abbrechen | `interface/back_001.ogg` |
| Hand durchblättern | `casino/card-fan-1.ogg`, alternativ `card-fan-2.ogg` |
| Karten mischen | `casino/card-shuffle.ogg`, passend zur jeweiligen Mischanimation takten |
| Karte ziehen | `casino/card-slide-1.ogg` bis `card-slide-4.ogg` |
| Karte ablegen | `casino/card-place-1.ogg` bis `card-place-4.ogg`, bei Ankunft auf dem Stapel |
| Ungültiger Spielzug | `interface/error_001.ogg`, kurz und leise |
| Nächster Spieler bereit | `interface/select_001.ogg` |
| Richtungswechsel | `interface/switch_001.ogg` |
| Aussetzen | `interface/pluck_001.ogg` |
| +2 / +4 | Kurzer Akzent plus zwei / vier zeitlich versetzte Ziehgeräusche |
| Joker | Eigenen kurzen Akzent aus den Pizzicato-Varianten auswählen |
| UNO: eine Karte übrig | Wiedererkennbares Signal aus den Pizzicato-Varianten auswählen |
| Spieler beendet seine Hand | Kurzer Erfolgston; unterscheiden vom Rundenende |
| Runde beendet | Passenden Pizzicato-Jingle auswählen |

## Einbau ins vorhandene Spiel

1. Kandidaten anhören, endgültige Signale auswählen und Lautstärken im Spiel abstimmen.
2. Einen zentralen Soundmanager mit `pygame.mixer` ergänzen; Dateien einmal
   vorladen. Das Spiel muss auch ohne verfügbares Audiogerät funktionieren.
3. Sounds an erfolgreiche Aktionen in `Kartenspiel/ui/anwendung.py` und an
   passende Animationszeitpunkte hängen. Nicht pro Zeichenaufruf abspielen.
4. Bei Kartenaktionen mehrere Varianten abwechseln. Dafür einen eigenen
   Zufallsgenerator verwenden, damit die Kartenreihenfolge unbeeinflusst bleibt.
5. Mute und Effektlautstärke im Start- und Pausenmenü ergänzen. Kurze Sperrzeiten
   verhindern Klick- und Fehlertonketten; bei Fokusverlust den Ton pausieren.
6. Finale Dateien nach `Kartenspiel/ui/assets/audio/` übernehmen und in
   `pyproject.toml` als Paketdaten aufnehmen. Die Auswahl hier dient zunächst
   der Vorbereitung und wird nicht mit dem installierten Spiel ausgeliefert.
7. Prüfen: gültige / ungültige Züge, Sonderkarten, UNO, Rundenende, übersprungene
   Mischanimation, Mute und Start ohne Audiogerät.

Hintergrundmusik ist eine eigene, optionale zweite Stufe: ein ruhiger Loop
mit separater Lautstärke und sanftem Ein-/Ausblenden. Die kurzen Jingles hier
sind keine Hintergrundmusik. Zuerst sollte das Spiel allein durch seine
Aktionssounds rund wirken.
