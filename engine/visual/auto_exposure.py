from array import array

import moderngl as mgl

from engine.shader_loader import load_shader

class AutoExposure:
    def __init__(self, ctx : mgl.Context, path):
        self.texture = ctx.texture((10, 10), 3)
        self.texture.filter = (mgl.NEAREST, mgl.NEAREST)
        self.framebuffer = ctx.framebuffer(self.texture)

        self.vbo = ctx.buffer(array('f', 
                [-1, -1, 0, 0,
                1, -1, 1, 0,
                -1, 1, 0, 1,
                1, 1, 1, 1
                ]))
        
        self.program_downscale = ctx.program(
            vertex_shader=load_shader(path, 'vert.glsl'),
            fragment_shader=load_shader(path, 'frag.glsl'))
        
        self.vao = ctx.vertex_array(self.program_downscale, [(self.vbo, '2f 2f', 'vert', 'texcoord')])

    def draw(self, tex):
        self.framebuffer.use()
        tex.use()
        self.vao.render(mgl.TRIANGLE_STRIP)