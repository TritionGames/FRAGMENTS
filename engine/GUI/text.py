import pygame as pg
import moderngl as mgl

from engine.renderer import create_buffer_rect, create_render_object
from engine.functions import surface_to_texture

class Text:
    def __init__(self, ctx, program, pos, text, font, color = (255, 255, 255)):
        self.x, self.y = pos
        self.ctx = ctx
        self.program = program
        self.text = text
        self.color = color
        self.font = font

    def init(self, resolution):        
        self.rendered_font = self.font.render(self.text, False, self.color).convert_alpha()

        rect = pg.Rect(self.x, self.y, *self.rendered_font.get_size())

        self.render_obj = create_render_object(self.ctx, self.program, create_buffer_rect(rect, resolution, self.ctx), surface_to_texture(self.rendered_font, self.ctx, 'BGRA'))
        
        del rect

    def render(self):
        self.render_obj.render()