import os
import math
import pickle

import time
from array import array

import pygame as pg
import pymunk as pm

from engine.renderer import Render, create_buffer_rect, create_render_object, create_buffer_line
from engine.functions import *
from engine.image_loader import images
from engine.physics import create_body
from engine.song_manager import *

class Block:
    def __init__(self, x, y, w, h, surface = None):
        self.rect = pg.FRect(x, y, w, h)
        self.resolution = (0, 0)
        self.rotate = 0
        self.block_type = 0
        self.static = True
        self.physics = False
        self.physics_type = pm.Body.STATIC
        self.physics_body = [None, None]
        self.spritesheet_level = 0
        self.mass = 100
        self.friction = 1
        self.collision = True
        self.light = None
        self.collision_type = 2
        self.physics_hitbox = None
        self.create_physics_body_in_init = True        
        self.programs = []
        self.fluid = False
        self.should_float = 0
        self.z = 1
        self.surface = surface
        self.instanced = False
        self.brightness = 1
        self.shininess = 1

    def default_update(self, game):
        if self.physics and not self.static:
            old_rect = (self.rect.copy(), self.rotate)
            self.set_rect_physics_pos()
            if old_rect != (self.rect, self.rotate):
                self.render_obj.vbo.release()
                self.render_obj.vao.release()
                self.render_obj.vbo = create_buffer_rect(self.rect, self.resolution, self.render_obj.ctx, math.degrees(self.physics_body[0].angle))
                self.render_obj.create_vao() 

            del old_rect
        
        self.update(game)

    def set_rect_physics_pos(self):
        if self.physics_body[0]:
            self.rect.x = self.physics_body[0].position.x + -1/2*self.physics_hitbox[0] + 25
            self.rect.y = -self.physics_body[0].position.y + -1/2*self.physics_hitbox[1] + 25

    def get_rect_physics_pos(self, physics_body, size):
        rect = pg.FRect(0, 0, *size)

        if physics_body[0]:
            rect.x = physics_body[0].position.x + -1/2*rect.w + 25
            rect.y = -physics_body[0].position.y + -1/2*rect.h + 25

        return rect
    
    def physics_pos_to_rect(self, position, size):
        return position[0] + -1/2*size[0] + 25, -position[1] + -1/2*size[1] + 25

    def extra_init(self, space):
        pass

        """
        this function is to include any extra init data without actually
        modifying the init function itself."""

    def init(self, ctx, program, resolution, space = None, set_physics_pos = True, programs = []):
        self.resolution = resolution

        if self.physics and self.create_physics_body_in_init:
            self.create_body(space, set_physics_pos)

        self.render_obj = self.create_renderer(ctx, program, self.rect, self.rotate if not (self.physics and self.create_physics_body_in_init) else self.physics_body[0].angle)

        self.programs = programs

        self.touching_water = False

        self.extra_init(space)

    def create_body(self, space = None, set_physics_pos = True, rect = None):
        rect = self.rect if not rect else rect

        if not self.physics_hitbox:
            self.physics_hitbox = rect.size

        self.physics_body = create_body((rect.x, -rect.y), self.physics_hitbox, self.physics_type, self.mass, self.friction, self.collision_type)
        self.physics_body[0].angle = math.radians(self.rotate)
        #self.physics_body[0].origin = self
        
        if space:
            space.add(*self.physics_body) 

        if set_physics_pos:
            self.set_rect_physics_pos()

    def create_renderer(self, ctx, program, rect, rotate = 0):
        render = Render()
        render.ctx = ctx
        render.program = program
        if self.surface:
            render.texture = surface_to_texture(self.surface.convert_alpha(), ctx, swizzle='BGRA')
        render.vbo = create_buffer_rect(rect, self.resolution, ctx, rotate if not self.physics else math.degrees(rotate))
        render.create_vao()

        return render

    def get_rect(self):
        return self.rect

    def add(self, objects):
        objects.append(self)

    def clear(self):
        if self.physics:
            self.physics_body[0].origin = None

        self.render_obj.clear()
        self.ctx = None
        self.programs = []
        self.surface = None

    def update(self, game):
        pass

    def render(self):
        self.render_obj.vao.program['z'] = self.z
        self.render_obj.vao.program['exposure'] = self.brightness
        self.render_obj.vao.program['shininess'] = self.shininess
        self.render_obj.render()

class Metal(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, surface)
        self.block_type = 0
        self.static = True
        self.physics = True
        self.collision = True
        self.friction = 0.85

class PoisonWater(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, surface)
        self.spritesheet_level = 2
        self.static = False
        self.physics = True
        self.collision = False
        self.fluid = True
        self.collision_type = 3
        self.physics_type = pm.Body.KINEMATIC

    def extra_init(self, space):
        self.global_time = 0
        self.render_obj.texture.repeat_x = True

        self.physics_body[1].sensor = True

    def update(self, game):
        self.global_time = game.seconds_passed

    def render(self):
        if self.global_time:
            self.programs[2]['offset'] = (self.global_time/3, 0)
        
        self.render_obj.render()

        if self.global_time:
            self.programs[2]['offset'] = (0, 0)

class Fan(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['fan'])
        self.block_type = -1
        self.static = False
        
        'fan'
        self.physics = False
        self.collision = False

    def update(self, game):
        self.rotate += game.dt * 100

        self.render_obj.vbo.release()
        self.render_obj.vao.release()
        self.render_obj.vbo = create_buffer_rect(self.rect, self.resolution, self.render_obj.ctx, self.rotate)
        self.render_obj.create_vao()

class Grass(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['grass'])
        self.block_type = -1
        self.static = False
        'grass'
        
        self.physics = False
        self.collision = False

class Dirt(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['dirt1'])
        self.block_type = -1
        self.static = False
        'dirt1'
        self.collision = False
        self.physics = False

class Bars(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['bars'])
        self.block_type = -1
        self.static = False
        self.collision = False
        'bars'

        self.physics = False

class Wires1(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['wires1'])
        self.block_type = -1
        self.static = False
        self.collision = False
        'wires1'
        self.physics = False
        self.z = 1.5

class Pipes(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, surface)
        self.static = False
        self.collision = False
        self.spritesheet_level = 1
        self.physics = False

class Cup(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['cup1'])
        self.block_type = -1
        self.static = False
        self.physics_type = pm.Body.DYNAMIC
        self.physics = True
        'cup1'
        self.mass = 20
        self.collision = False
        self.friction = 0.94
        self.collision_type = 2

    def update(self, game):
        self.set_rect_physics_pos()

        self.render_obj.vbo.release()
        self.render_obj.vao.release()
        self.render_obj.vbo = create_buffer_rect(self.rect, self.resolution, self.render_obj.ctx, math.degrees(self.physics_body[0].angle))
        self.render_obj.create_vao() 

class Light1(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['lightbulb'])
        self.block_type = -1
        self.static = False
        self.physics_type = pm.Body.DYNAMIC
        self.physics = False
        'lightbulb'

        self.mass = 10
        self.collision = False
        self.friction = 1
        self.light = [self.rect.center, (3, 3, 3)]

class Crate(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['crate'])
        self.block_type = -1
        self.static = False
        self.physics_type = pm.Body.DYNAMIC
        self.physics = True
        'crate'
        self.mass = 70
        self.collision = False
        self.friction = 0.7
        self.collision_type = 2

class CrateSmall(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['crate'])
        self.block_type = -1
        self.static = False
        self.physics_type = pm.Body.DYNAMIC
        self.physics = True
        'crate'
        self.mass = 45
        self.collision = False
        self.friction = 0.7
        self.collision_type = 2

    def update(self, game):
        #print(self.physics_body[0].position, type(self))

        self.set_rect_physics_pos()

        self.render_obj.vbo.release()
        self.render_obj.vao.release()
        self.render_obj.vbo = create_buffer_rect(self.rect, self.resolution, self.render_obj.ctx, math.degrees(self.physics_body[0].angle))
        self.render_obj.create_vao() 

class Turret(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['turretbase'])
        self.block_type = -1
        self.static = False
        self.physics_type = pm.Body.DYNAMIC
        self.physics = True
        'turretbase'

        self.mass = 30
        self.collision = False
        self.friction = 0.5
        self.collision_type = 2
        self.create_physics_body_in_init = False

    def extra_init(self, space):
        self.create_body(space, rect = pg.Rect(self.rect.x, self.rect.y, 30, 16), set_physics_pos=False)

        self.render_obj_head = self.create_renderer(self.render_obj.ctx, self.render_obj.program, 'turrethead', pg.Rect(self.rect.x, self.rect.y, 30, 16))
        self.target_angle = 0

        self.physics_body[0].position = (self.physics_body[0].position[0], self.physics_body[0].position[1])
        self.physics_body[0].moment = 3000

        self.anchor = pm.Body(body_type=pm.Body.STATIC)
        self.anchor.position = self.physics_body[0].position

        self.pinJoint = pm.PinJoint(self.physics_body[0], self.anchor)

        if self.physics_body[0].space:
            self.physics_body[0].space.add(self.pinJoint)

        self.rotational_speed = 0
        self.attached = True

        self.line_render = None
        self.flare_render = None

        self.state = 'neutral'
        self.forget_time = 2
        self.look_around = 1
        self.look_around_total = 5
        self.look_around_times = 0

        self.player_direction = 0

        self.rot_force = 15

        self.light = [(0, 0), 0, (0, 0, 0)]

        self.toggle_seeking = False

        self.shoot_timer = 0
        self.firerate = 0.2

    def shoot(self, game):
        if time.time() - self.shoot_timer > self.firerate:
            self.shoot_timer = time.time()

            play_sound(game.sounds['turret shoot'])

    def damp(self, body, gravity, damping, dt):
        mod_damp = body.custom_damping * damping
        pm.Body.update_velocity(body, gravity, mod_damp, dt)

    def update(self, game):
        self.render_obj_head.vbo.release()
        self.render_obj_head.vao.release()

        self.head_rect = self.get_rect_physics_pos(self.physics_body, (30, 16))

        self.target_angle = math.degrees(self.physics_body[0].angle)

        self.render_obj_head.vbo = create_buffer_rect(self.head_rect, self.resolution, self.render_obj.ctx, self.target_angle, raw = True)

        self.render_obj_head.vbo = self.render_obj.ctx.buffer(data=array('f', self.render_obj_head.vbo))
        self.render_obj_head.create_vao() 

        if self.pinJoint.impulse > 10000 and self.attached:
            self.attached = False
            self.physics_body[0].custom_damping = 1
            self.line_render = None 
            self.physics_body[1].filter = pm.ShapeFilter(categories=4294967295)
            self.physics_body[0].space.remove(self.pinJoint)

        if self.attached:
            self.physics_body[0].custom_damping = 0.6
            self.physics_body[0].velocity_func = self.damp

            if self.line_render:
                self.line_render.clear()

            if self.flare_render:
                self.flare_render.clear(texture=False)

            self.physics_body[1].filter = pm.ShapeFilter(categories=0b1)

            angle_pos = [self.physics_body[1].bb.center().x, self.physics_body[1].bb.center().y]

            angle_pos[0] -= math.cos(self.physics_body[0].angle) * 1000
            angle_pos[1] -= math.sin(self.physics_body[0].angle) * 1000

            start = list(self.physics_body[1].bb.center())

            self.seg_q = self.physics_body[0].space.segment_query_first(start, angle_pos, 1, pm.ShapeFilter(mask=pm.ShapeFilter.ALL_MASKS() ^ 0b1))

            point = None

            if self.seg_q:  
                point_raw = [*self.seg_q.point]

                point = self.physics_pos_to_rect(point_raw, (0, 0))

                if self.seg_q.shape.collision_type == 1:
                    self.state = 'attack'
                    self.forget_time = 2

                #self.light = game.emit_light(point, 0.025, (30, 0, 0))

                #self.flare_render = create_render_object(self.render_obj.ctx, self.programs[2], create_buffer_rect((point_flare[0] - 0.5, point_flare[1] - 0.5, 16, 16), self.resolution, self.render_obj.ctx), game._mgl_images['red_flare'])
                
            angle_pos = self.physics_pos_to_rect(angle_pos, (0, 0))

            self.line_render = create_render_object(self.render_obj.ctx, self.programs[5], create_buffer_line(self.head_rect.center, point if point else angle_pos, self.resolution, self.render_obj.ctx), create_vao=False)
            self.line_render.create_vao(['2f', 'vert'])
            self.line_render.mode = mgl.LINES

            if self.forget_time <= 0:
                self.state = 'neutral'
                self.forget_time = 0

            else:
                self.forget_time -= game.dt

            if self.state == 'attack':
                self.shoot(game)


    def render(self):
        self.render_obj.render()

        if self.attached:
            if self.line_render:
                self.line_render.render()

        self.render_obj_head.render()

class Phone(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, images['phone'])
        self.block_type = -1
        self.static = False
        self.collision = False
        'phone'

        self.physics = False

class Image(Block):
    def __init__(self, x, y, w, h, surface = None):
        super().__init__(x, y, w, h, surface)
        self.block_type = -1
        self.static = False
        self.collision = False
        self.physics = False
        self.surface = surface
