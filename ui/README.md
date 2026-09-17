# UNO-Oberfläche

Im Ordner `ui` starten:

```sh
uv run uno-ui
```

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
