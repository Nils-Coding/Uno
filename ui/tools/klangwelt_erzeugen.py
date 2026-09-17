"""Erzeugt die eigenen musikalischen UNO-Akzente und einen nahtlosen Loop.

Nur Python-Standardbibliothek; die Kenney-Geräusche bleiben unverändert.
Aufruf im Projektordner: python tools/klangwelt_erzeugen.py
"""

from array import array
import math
from pathlib import Path
import sys
import wave


RATE = 22050
ZIEL = Path(__file__).resolve().parents[1] / "Kartenspiel/ui/assets/audio"


def ton(puffer, beginn, note, dauer, pegel, loop=False):
    frequenz = 440 * 2 ** ((note - 69) / 12)
    for i in range(int(dauer * RATE)):
        t = i / RATE
        # Weicher Anschlag, abklingende Obertöne, Ende ohne Knacksen.
        huelle = min(1, t / 0.008) * math.exp(-4 * t / dauer)
        huelle *= min(1, (dauer - t) / 0.04)
        phase = math.tau * frequenz * t
        signal = math.sin(phase) + 0.22 * math.sin(2 * phase) + 0.06 * math.sin(3 * phase)
        index = round(beginn * RATE) + i
        if loop:
            index %= len(puffer)
        if index < len(puffer):
            puffer[index] += pegel * huelle * signal


def speichern(name, puffer):
    spitze = max(abs(x) for x in puffer) or 1
    faktor = min(1, 0.7 / spitze)
    samples = array("h", (round(x * faktor * 32767) for x in puffer))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(ZIEL / f"{name}.wav"), "wb") as datei:
        datei.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        datei.writeframes(samples.tobytes())


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    motive = {
        "bereit": [(0, 72), (0.09, 76)],
        "joker": [(0, 67), (0.10, 72), (0.20, 76)],
        "uno": [(0, 79), (0.16, 84)],
        "richtung": [(0, 72), (0.09, 67), (0.18, 72)],
        "aussetzen": [(0, 64), (0.12, 60)],
        "strafe": [(0, 55), (0.08, 60)],
        "fertig": [(0, 72), (0.14, 76), (0.28, 79)],
        "sieg": [(0, 72), (0.16, 76), (0.32, 79), (0.56, 84), (0.56, 76), (0.56, 79)],
        "ende": [(0, 67), (0.18, 64), (0.36, 60)],
    }
    for name, noten in motive.items():
        puffer = [0.0] * round((max(t for t, _ in noten) + 0.75) * RATE)
        for beginn, note in noten:
            ton(puffer, beginn, note, 0.7, 0.24)
        speichern(name, puffer)

    # Acht Takte bei 100 BPM, Cmaj7 – Am7 – Fmaj7 – G6.
    schlag = 0.6
    puffer = [0.0] * round(32 * schlag * RATE)
    for takt, akkord in enumerate(((60, 64, 67, 71), (57, 60, 64, 67),
                                   (53, 57, 60, 64), (55, 59, 62, 64)) * 2):
        anfang = takt * 4 * schlag
        ton(puffer, anfang, akkord[0] - 12, 2.6, 0.17, loop=True)
        for schritt, index in enumerate((0, 2, 1, 3)):
            ton(puffer, anfang + (schritt + 0.5) * schlag,
                akkord[index] + 12, 1.4, 0.11, loop=True)
    speichern("tischmusik", puffer)


if __name__ == "__main__":
    main()
