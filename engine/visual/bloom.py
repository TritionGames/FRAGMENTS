from array import array

import moderngl as mgl
import pygame as pg

from engine.shader_loader import load_shader

class Mip:
    def __init__(self, ctx, vbo, res, program_downscale, program_mix):
        self.tex = ctx.texture(res, 3, dtype='f2')
        
        self.tex.repeat_x, self.tex.repeat_y = False, False
        self.fbo = ctx.framebuffer(self.tex)

        self.vao = ctx.vertex_array(program_downscale, [(vbo, '2f 2f', 'vert', 'texcoord')])
        self.mix_vao = ctx.vertex_array(program_mix, [(vbo, '2f 2f', 'vert', 'texcoord')])
        
        self.res = res

    def release(self):
        self.tex.release()
        self.fbo.release()
        self.vao.release()
        self.mix_vao.release()
        self.res = None

class Bloom:
    def __init__(self, ctx, path, resolution, levels):
        self.ctx = ctx

        self.vbo = ctx.buffer(array('f', 
                [-1, -1, 0, 0,
                1, -1, 1, 0,
                -1, 1, 0, 1,
                1, 1, 1, 1
                ]))

        self.program_downscale = ctx.program(
            vertex_shader=load_shader(path, 'vert.glsl'),
            fragment_shader=load_shader(path, 'downscale.frag.glsl'))

        self.program_mix = ctx.program(
            vertex_shader=load_shader(path, 'vert.glsl'),
            fragment_shader=load_shader(path, 'mix.frag.glsl'))
        
        self.program_highlights = ctx.program(
            vertex_shader=load_shader(path, 'vert.glsl'),
            fragment_shader=load_shader(path, 'highlights.frag.glsl'))

        self.highlights_vao = ctx.vertex_array(self.program_highlights, [(self.vbo, '2f 2f', 'vert', 'texcoord')])
        self.highlights_tex = ctx.texture(resolution, 3, dtype='f2')
        self.highlights_fbo = ctx.framebuffer(self.highlights_tex)

        self.resolution = resolution
        self.levels = levels
        self.mips = []

        self.amplifier = 4

        self.generate_mips()

    def generate_mips(self):
        for mip in self.mips:
            mip.release()

        self.mips = []

        for i in range(self.levels):
            self.mips.append(Mip(self.ctx, self.vbo, (int(self.resolution[0] / ((i * self.amplifier +1))), int(self.resolution[1] / ((i * self.amplifier+1)))), self.program_downscale, self.program_mix))
