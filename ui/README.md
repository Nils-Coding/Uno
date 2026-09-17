# UNO-Oberfläche

Im Ordner `ui` starten:

```sh
uv run uno-ui
```

## Sound und Musik

Karten-, Menü- und Sonderkartengeräusche sind integriert. Ablegen erklingt bei
der Landung der Karte; +2/+4 lösen eine kurze Ziehfolge aus. UNO, abgeschlossene
Hände und das Rundenende haben eigene musikalische Signale.

- **M** schaltet den gesamten Ton stumm oder wieder ein, auch während Animationen.
- Im **Start- und Pausenmenü** lassen sich Effekte und Musik separat regeln.
- Die optionale Hintergrundmusik ist beim ersten Start ausgeschaltet.
- Einstellungen bleiben zwischen Spielstarts erhalten. Unter macOS liegen sie
  in `~/Library/Application Support/uno-kartenspiel/audio.json`, sonst in
  `~/.config/uno-kartenspiel/audio.json`.
- Bei Fokusverlust pausieren Audio und Animationen; ohne Audiogerät bleibt
  das Spiel vollständig bedienbar.

Die Kartengeräusche und UI-Effekte stammen von Kenney (CC0).
Quellen und Lizenzen liegen unter `Kartenspiel/ui/assets/audio/`.
Musikalische Motive und Hintergrundloop werden mit
`python tools/klangwelt_erzeugen.py` reproduzierbar erzeugt und sind als WAVs
mitgeliefert. Zum Spielen sind weder Downloads noch zusätzliche Pakete nötig.

## Spielgefühl und Revanche

- Spielerwechsel und Handaufdecken sind still; das längere Fächergeräusch
  wird nicht mehr verwendet.
- Die aktive Farbe beleuchtet den Tisch. Karten heben sich beim Überfahren
  sanft an und landen mit einem kurzen Lichtimpuls auf der Ablage.
- Sonderkarten, UNO und abgeschlossene Hände bekommen einen kurzen visuellen
  Akzent. Währenddessen sind weitere Spielzüge gesperrt.
- Links stehen die letzten drei öffentlichen Aktionen. Gezogene Karten
  bleiben geheim, ebenso die Hand bis zum bewussten Aufdecken.
- Das Finale zeigt Pokal, Konfetti, Aktionen, Spielzeit und Siege der Serie.
  „Revanche“ behält die Siegesserie. Eine andere Spielerzahl beginnt eine neue
  Serie; die Siege gelten nur für die aktuelle Sitzung.

## Tests

Tests einschließlich des installierten Startbefehls:

```sh
uv run python -m unittest discover -s tests -v
```

## macOS: `No module named 'Kartenspiel'`

Bei der Fehlersuche waren die `.pth`-Dateien in `.venv` mit dem macOS-Attribut
`hidden` markiert. Der verwendete Python-Interpreter überspringt solche Dateien.
Dadurch fehlt die Verbindung zum Quellcode, obwohl `uv` das Projekt als
installiert erkennt. Ein Start über `python main.py` kann den Fehler verdecken,
weil Python dabei direkt im Quellordner sucht.

Falls dieses Attribut erneut gesetzt wurde, im Ordner `ui` gezielt entfernen:

```sh
chflags nohidden .venv/lib/python*/site-packages/*.pth
uv run uno-ui
```

Beim Ausblenden von `.venv` das Attribut nur am Ordner setzen, nicht rekursiv
an dessen Inhalt. Der Punkt am Anfang des Ordnernamens blendet `.venv` bereits
standardmäßig im Finder aus.

`tests/test_installation.py` prüft den installierten Startbefehl in einem
isolierten Python-Prozess außerhalb des Quellordners. So wird eine defekte
Installation nicht durch den Testaufruf aus dem Projektordner verdeckt.
