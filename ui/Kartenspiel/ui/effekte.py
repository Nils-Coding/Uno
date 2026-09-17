"""Kleine, zeitbasierte Effekte ohne Einfluss auf den Spielzufall."""

from functools import lru_cache
import math

import pygame


@lru_cache(maxsize=8)
def tischlicht(farbe):
    bild = pygame.Surface((520, 370), pygame.SRCALPHA)
    for inset in range(0, 145, 5):
        pygame.draw.ellipse(bild, (*farbe, 2 + inset // 8),
                            (inset, inset * 0.65, 520 - inset * 2, 370 - inset * 1.3))
    return bild


def impuls(flaeche, alter, farbe, position=(819, 404)):
    if not 0 <= alter < 0.65:
        return
    t = alter / 0.65
    bild = pygame.Surface((440, 440), pygame.SRCALPHA)
    pygame.draw.circle(bild, (*farbe, round(150 * (1 - t) ** 2)), (220, 220),
                       round(85 + 110 * (1 - (1 - t) ** 3)), 2)
    for i in range(16):
        winkel = i * math.tau / 16
        radius = 105 + 95 * t
        punkt = (round(220 + math.cos(winkel) * radius), round(220 + math.sin(winkel) * radius))
        pygame.draw.circle(bild, (*farbe, round(190 * (1 - t))), punkt, max(1, round(3 * (1 - t))))
    flaeche.blit(bild, (position[0] - 220, position[1] - 220))


def pokal(flaeche, mitte, farbe):
    x, y = mitte
    pygame.draw.arc(flaeche, farbe, (x - 55, y - 28, 42, 46), math.pi / 2, math.pi * 1.5, 5)
    pygame.draw.arc(flaeche, farbe, (x + 13, y - 28, 42, 46), -math.pi / 2, math.pi / 2, 5)
    pygame.draw.polygon(flaeche, farbe, [(x - 35, y - 33), (x + 35, y - 33),
                                      (x + 25, y + 13), (x, y + 29), (x - 25, y + 13)])
    pygame.draw.rect(flaeche, farbe, (x - 5, y + 24, 10, 24), border_radius=3)
    pygame.draw.rect(flaeche, farbe, (x - 27, y + 46, 54, 8), border_radius=4)
    pygame.draw.line(flaeche, (255, 245, 191), (x - 23, y - 24), (x - 18, y + 2), 4)


def konfetti(flaeche, alter, farben):
    if not 0 <= alter < 5:
        return
    bild = pygame.Surface(flaeche.get_size(), pygame.SRCALPHA)
    alpha = round(220 * min(1, (5 - alter) / 1.5))
    for i in range(76):
        t = alter - (i % 7) * 0.035
        if t < 0:
            continue
        seite = -1 if i % 2 else 1
        vx = seite * (45 + (i * 47 % 260))
        vy = -180 - (i * 31 % 280)
        x = 720 + seite * 220 + vx * t + math.sin(t * 3 + i) * 16
        y = 315 + vy * t + 135 * t * t
        groesse = 4 + i % 5
        punkte = []
        for dx, dy in ((-1, -0.45), (1, -0.45), (1, 0.45), (-1, 0.45)):
            winkel = i + t * (2 + i % 4)
            punkte.append((x + (dx * math.cos(winkel) - dy * math.sin(winkel)) * groesse,
                           y + (dx * math.sin(winkel) + dy * math.cos(winkel)) * groesse))
        pygame.draw.polygon(bild, (*farben[i % len(farben)], alpha), punkte)
    flaeche.blit(bild, (0, 0))
