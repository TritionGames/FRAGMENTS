import pygame as pg
from pygame.locals import *

def get_tile_at_index(i: int, spritesheet: pg.Surface, size: tuple = (50, 50), increment: int = 50, y_level = 0):
    surface = pg.Surface(size, SRCALPHA)

    surface.blit(spritesheet, (-increment*i, -increment*y_level, *size))

    return surface