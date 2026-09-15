from functools import lru_cache
from pathlib import Path

import pygame

from ..karte import Karte
from ..sonderkarte import Sonderkarte

FARBNAMEN = {"blau": "Blue", "rot": "Red", "grün": "Green", "gelb": "Yellow"}
AKTIONEN = {"ziehen": "Draw", "Aussetzen": "Skip", "Richtungswechsel": "Reverse"}


def dateiname(karte: Karte) -> str:
    if karte.getFarbe() == "schwarz":
        return "Wild_Draw.png" if karte.getWert() == "4" else "Wild.png"
    wert = AKTIONEN[karte.get_Funktion()] if isinstance(karte, Sonderkarte) else karte.getWert()
    return f"{FARBNAMEN[karte.getFarbe()]}_{wert}.png"


class Assets:
    def __init__(self) -> None:
        self.ordner = Path(__file__).with_name("assets")
        self.original = lru_cache(maxsize=64)(self.original)
        self.bild = lru_cache(maxsize=256)(self.bild)
        self.karte = lru_cache(maxsize=512)(self.karte)

    def original(self, name: str) -> pygame.Surface:
        return pygame.image.load(self.ordner / name).convert_alpha()

    def bild(self, name: str, breite: int, hoehe: int) -> pygame.Surface:
        return pygame.transform.smoothscale(self.original(name), (breite, hoehe))

    def karte(
        self, name: str, hoehe: int = 190, winkel: float = 0, markiert: bool = False
    ) -> pygame.Surface:
        breite = round(hoehe * 388 / 562)
        bild = pygame.Surface((breite + 24, hoehe + 28), pygame.SRCALPHA)
        pygame.draw.rect(bild, (0, 0, 0, 65), (7, 10, breite + 10, hoehe + 12), border_radius=14)
        pygame.draw.rect(bild, (0, 0, 0, 80), (10, 10, breite + 4, hoehe + 6), border_radius=12)
        if markiert:
            pygame.draw.rect(
                bild, (208, 239, 151), (8, 4, breite + 8, hoehe + 8), width=3, border_radius=12
            )
        bild.blit(self.bild(name, breite, hoehe), (12, 8))
        return pygame.transform.rotozoom(bild, winkel, 1)
