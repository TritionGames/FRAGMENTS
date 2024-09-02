import os

import pygame as pg

from engine.functions import surface_to_texture
from engine.GUI.font import font
from engine.renderer import create_render_object, create_buffer_rect

pg.mixer.pre_init(44100, -16, 2, 512)
pg.mixer.init()
pg.init()

class Button:
    def __init__(self, ctx, resolution, program, pos, text, hover_sound):
        self.ctx = ctx
        self.resolution = resolution
        self.program = program
        self.rect = pg.Rect(*pos, 0, 0)
        self.text = text
        self.color = (255, 255, 255)
        self.play_sound = False
        self.sound_hover = hover_sound

    def init(self):
        self.render_obj = None
        self.update_text()

    def generate_text(self):
        self.rendered_text = font.render(self.text, False, self.color).convert_alpha()
        return self.rendered_text

    def update_text(self):
        self.rendered_text = font.render(self.text, False, self.color).convert_alpha()

        r_w = self.rendered_text.get_width()
        r_h = self.rendered_text.get_height()

        self.rect.size = r_w, r_h

        if self.render_obj:
            self.render_obj.clear()
            
        self.render_obj = create_render_object(self.ctx, self.program, 
                                               create_buffer_rect((self.rect), self.resolution, self.ctx), 
                                               surface_to_texture(self.rendered_text, self.ctx, 'BGRA'))
        
    def update(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            return True

        return False
    
    def render(self, mouse_pos):
        
        if not self.play_sound and self.update(mouse_pos):
            self.play_sound = True
            self.sound_hover.play()
            
        elif not self.update(mouse_pos) and self.play_sound:
            self.play_sound = False

        self.render_obj.render()