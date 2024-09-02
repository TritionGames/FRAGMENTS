import os

import pygame as pg
import math
import pymunk as pm
import moderngl as mgl

from engine.renderer import Render, create_render_object, create_buffer_rect, create_buffer_line, relative_coord
from engine.functions import surface_to_texture
from engine.image_loader import load_image
from engine.physics import create_body

class Player:
    def __init__(self, x, y):
        super().__init__()
        self.rect = pg.FRect(x, y, 30, 30)
        self.health = 100
        self.render_obj = Render()
        self.resolution = (0, 0)
        self.instance_id = 1
        self.collision_types = {'bottom': False, 'top': False, 'right': False, 'left': False}
        self.physics_type = pm.Body.DYNAMIC
        self.collision_type = 1
        self.coyote_time = 0
        self.physics_body = [0, 0]
        self.physics_hitbox = [30, 30]
        self.line_render = None
        self.programs = []
        self.grabbed_body = None
        self.pinJoint = None
        self.touching_water = False
        self.grab_pos = (0, 0)
        self.grab_distance = 75
        self.arbiter = None

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
    
    def rect_pos_to_physics(self, position, size):
        return position[0] - -1/2*size[0] + 25, -position[1] - -1/2*size[1] + 25

    def init(self, ctx, program, resolution, space, programs):
        self.resolution = resolution
        self.render_obj.texture = surface_to_texture(load_image(os.getcwd(), 'player.png'), ctx)
        self.render_obj.ctx = ctx
        self.render_obj.program = program
        self.render_obj.vbo = create_buffer_rect(pg.Rect(self.resolution[0]/2, self.resolution[1]/2, *self.rect.size), self.resolution, ctx)
        self.render_obj.create_vao()
        self.can_jump = False

        self.physics_body = create_body((self.rect.x, -self.rect.y), (self.rect.w, self.rect.h), self.physics_type, 25, 0.5, 1, float('inf'), elasticity=0.6)
        self.physics_body[0].moment = float('inf')
        self.physics_body[0].origin = self

        if space:
            space.add(*self.physics_body)        

        self.collision_handler = space.add_collision_handler(2, 1)
        self.collision_handler.begin = self.is_touching_ground
        self.collision_handler.separate = self.left_touching_ground

        self.touching_count = 0

        self.programs = programs

    def add(self, objects):
        objects.append(self)

    def remove(self):
        del self

    def is_touching_ground(self, arbiter, space, data):
        self.on_body = arbiter.shapes[0].body

        return True
    
    def left_touching_ground(self, arbiter, space, data):
        return True

    def jump(self):
        if (self.coyote_time < 0.1 or self.touching_count > 0):
            self.physics_body[0].velocity = [self.physics_body[0].velocity[0], 0]
            self.physics_body[0].apply_impulse_at_world_point((0, 12000), self.physics_body[0].position)
            self.on_body.apply_impulse_at_world_point((0, -12000), self.on_body.position)
            #self.can_jump = False
            self.coyote_time = 100
        #    self.coyote_time = 100

    def zero_gravity(self, body, gravity, damping, dt):
        pm.Body.update_velocity(body, (0,0), damping, dt)

    def default_velocity(self, body, gravity, damping, dt):
        mod_damp = body.custom_damping * damping
        pm.Body.update_velocity(body, gravity, mod_damp, dt)

    def update(self, game):

        self.set_rect_physics_pos()

        if not self.can_jump:
            self.coyote_time += game.dt

        if self.render_obj.vbo:
            self.render_obj.vbo.release()
        
        #self.render_obj.vbo = create_buffer_rect(self.rect, self.resolution, self.render_obj.ctx)
        #self.render_obj.create_vao()

        self.physics_body[1].filter = pm.ShapeFilter(categories=0b111)

        angle_pos = [self.physics_body[1].bb.center().x, self.physics_body[1].bb.center().y]

        direction = math.atan2(game.mouse_pos[1] - game.resolution[1]/2, game.mouse_pos[0] - game.resolution[0]/2)

        angle_pos[0] += math.cos(direction) * self.grab_distance
        angle_pos[1] -= math.sin(direction) * self.grab_distance

        start = list(self.physics_body[1].bb.center())

        self.seg_q = self.physics_body[0].space.segment_query_first(start, angle_pos, 1, pm.ShapeFilter(mask=pm.ShapeFilter.ALL_MASKS() ^ 0b111))

        bb = self.physics_body[1].bb

        self.touching_ground = self.physics_body[0].space.segment_query_first([bb.left + 2, bb.bottom], [bb.right - 2, bb.bottom], 1, pm.ShapeFilter(mask=pm.ShapeFilter.ALL_MASKS() ^ 0b111))

        if self.touching_ground:
            self.coyote_time = 0

        if self.line_render:
            self.line_render.clear()


        if self.seg_q:  
            point_raw = [*self.seg_q.point]

            point = self.rect_pos_to_physics(point_raw, (0, 0))

            self.line_render = create_render_object(self.render_obj.ctx, self.programs[5], create_buffer_line(self.rect.center, point, self.resolution, self.render_obj.ctx), create_vao=False)
            self.line_render.create_vao(['2f', 'vert'])
            self.line_render.mode = mgl.LINES

            if pg.mouse.get_just_pressed()[0]:
                self.seg_q.shape.body.apply_force_at_world_point((math.cos(direction) * 5000000, -math.sin(direction) * 5000000), self.seg_q.shape.body.position)

            if pg.mouse.get_just_pressed()[2]:
                if not self.grabbed_body and not self.pinJoint and self.seg_q.shape.body.body_type == pm.Body.DYNAMIC:
                    self.grabbed_body = self.seg_q.shape.body
                    self.pinJoint = pm.PinJoint(self.grabbed_body, self.physics_body[0])
                    game.space.add(self.pinJoint)

        if not pg.mouse.get_pressed()[2]:
            if self.pinJoint:
                self.release_grabbed_object()

    def release_grabbed_object(self):
        self.grabbed_body.space.remove(self.pinJoint)
        self.pinJoint = None
        self.grabbed_body = None

    def render(self):
        self.render_obj.program['position'] = relative_coord(self.rect.topleft, self.resolution, self.render_obj.ctx)
        self.render_obj.render()
        self.render_obj.program['position'] = (0, 0)
        if self.line_render:
            self.programs[5]['color'] = (0, 1, 0, 1)
            self.line_render.render()
            self.programs[5]['color'] = (1, 0, 0, 0.8)