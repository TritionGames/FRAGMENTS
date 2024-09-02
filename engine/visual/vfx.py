import time

import pygame as pg

from engine.image_loader import images
from engine.renderer import create_render_object, create_buffer_rect
from engine.functions import surface_to_texture

class Splash:
    def __init__(self, pos, ctx, program, resolution):
        self.rect = pg.Rect(*pos, 30, 30)
        self.frame = 0
        self.image_name = 'splash'
        self.frame_change = 0.1
        self.frame = 0
        self.max_frames = 5
        self._last_changed = 0
        self.ctx = ctx
        self.program = program
        self.resolution = resolution
        self.render_obj = None

    def update(self, vfx):
        if time.time() - self._last_changed > self.frame_change:
            self.frame += 1
            self._last_changed = time.time()

            if self.frame > self.max_frames:
                self.render_obj.clear()
                vfx.remove(self)

            else:
                if self.render_obj:
                    self.render_obj.clear()

                self.render_obj = create_render_object(self.ctx, self.program, create_buffer_rect(self.rect, self.resolution, self.ctx), surface_to_texture(images[f'splash{int(self.frame)}'], self.ctx))

    def render(self):
        self.render_obj.render()
