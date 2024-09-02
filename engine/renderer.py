import os
import math
from array import array

import moderngl as mgl

from engine.image_loader import load_image

spritesheet = load_image(os.getcwd(), 'spritesheet.png')

class Render:
    def __init__(self):
        self._ctx = None
        self._program = None
        self._vbo = None
        self._vao = None
        self._texture = None
        self._mode = mgl.TRIANGLE_STRIP

        self.instances = 1

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, tex):
        self._texture = tex

    @property
    def vao(self):
        return self._vao

    @vao.setter
    def vao(self, vao):
        self._vao = vao

    @property
    def vbo(self):
        return self._vbo

    @vbo.setter
    def vbo(self, vbo):
        self._vbo = vbo

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):    
        self._mode = mode

    @property
    def program(self):
        return self._program
    
    @program.setter
    def program(self, program):
        self._program = program

    @property
    def ctx(self):
        return self._ctx
    
    @ctx.setter
    def ctx(self, ctx):
        self._ctx = ctx
    
    def create_vao(self, attrs = ['2f 2f', 'vert', 'texcoord']):
        if self.vao:
            self.vao.release()
        self.vao = self._ctx.vertex_array(self.program, [(self.vbo, *attrs)])

    def render(self):
        if self.texture:
            self.texture.use()

        if self.vao:
            self.vao.render(mode=self.mode, instances=self.instances)

    def clear(self, texture = True):
        if self.texture and texture:
            self.texture.release()
            self.texture = None

        if self.vao:
            self.vao.release()
            self.vao = None

        if self.vbo:
            self.vbo.release()
            self.vbo = None
        
        self.ctx = False
        self.program = False

def rotate_buffer(buffer, angle, origin, aspect_ratio):
    # Convert angle to radians
    theta = math.radians(angle)
    
    # Precompute cos and sin of the angle
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)
    
    # Origin coordinates
    ox, oy = origin
    
    # Aspect ratio
    aspect_x, aspect_y = aspect_ratio
    
    # Rotated buffer
    rotated_buffer = []
    
    # Iterate over the buffer and apply the rotati on matrix to each position
    for i in range(0, len(buffer), 4):
        # Original position coordinates
        x = buffer[i]
        y = buffer[i + 1]
        
        # UV coordinates remain unchanged
        u = buffer[i + 2]
        v = buffer[i + 3]
        
        # Translate point to origin
        x_translated = x - ox
        y_translated = y - oy
        
        # Normalize aspect ratio
        x_normalized = x_translated / aspect_x
        y_normalized = y_translated / aspect_y
        
        # Apply rotation
        x_rot = x_normalized * cos_theta - y_normalized * sin_theta
        y_rot = x_normalized * sin_theta + y_normalized * cos_theta
        
        # De-normalize aspect ratio
        x_final = x_rot * aspect_x + ox
        y_final = y_rot * aspect_y + oy
        
        # Append the rotated coordinates and the unchanged UV coordinates
        rotated_buffer.extend([x_final, y_final, u, v])
    
    return rotated_buffer

def relative_coord(coord, resolution, ctx):
    win_w, win_h = resolution
    l, t = coord
    r_w_w = 1 / win_w
    r_w_h = 1 / win_h
    no_t = (t * r_w_h) * -2 + 1
    no_l = (l * r_w_w) * 2 - 1

    return no_l, no_t

def create_buffer_rect(rect, resolution, ctx, rotate = 0, raw = False, image_id = None, rotate_origin = None):
    win_w, win_h = resolution
    l, t, r, b = rect
    r_w_w = 1 / win_w
    r_w_h = 1 / win_h
    no_t = (t * r_w_h) * -2 + 1
    no_b = ((t + b) * r_w_h) * -2 + 1
    no_l = (l * r_w_w) * 2 - 1
    no_r = ((r + l) * r_w_w) * 2 - 1 

    if image_id == None:
        buffer = [
                # position (x, y), uv coords (x, y)
                no_l, no_t, 0, 0,  # topleft
                no_r, no_t, 1, 0,  # topright
                no_l, no_b, 0, 1,  # bottomleft
                no_r, no_b, 1, 1,  # bottomright
            ]
    else:
            buffer = [
            # position (x, y), uv coords (x, y)
            no_l, no_t, 0, 0, image_id,  # topleft
            no_r, no_t, 1, 0, image_id,  # topright
            no_l, no_b, 0, 1, image_id,  # bottomleft
            no_r, no_b, 1, 1, image_id,  # bottomright
        ]
    if rotate:
        x, y = relative_coord(rect.center if not rotate_origin else rotate_origin, resolution, ctx)
        buffer = rotate_buffer(buffer, rotate, (x, y), (9, 16))

    return ctx.buffer(data=array('f', buffer)) if not raw else buffer

def create_buffer_line(point1, point2, resolution, ctx, slice = 0):
    p1 = relative_coord(point1, resolution, ctx)
    p2 = relative_coord(point2, resolution, ctx)

    buffer = [p1[0], p1[1],
              p2[0], p2[1],]
    
    return ctx.buffer(data=array('f', buffer))

def create_render_object(ctx, program, vbo = None, texture = None, create_vao = True):
    renderer = Render()
    renderer.ctx = ctx
    renderer.program = program
    renderer.vbo = vbo
    renderer.rotate = 0
    renderer.texture = texture
    if create_vao:
        renderer.create_vao()
    return renderer
