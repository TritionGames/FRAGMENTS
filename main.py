import os
import time
import threading
import glm
import multiprocessing
from copy import deepcopy

import moderngl as _mgl
import pygame as _pg
from pygame.locals import *
from cProfile import Profile
from pstats import SortKey, Stats
import multiprocessing

from engine.shader_loader import load_shader
from engine.image_loader import load_image, load_images_mgl
from objects.player_class import Player
from objects.block_class import *
from engine.functions import physics_pos_to_rect
from engine.key_inputs import keybinds
from engine.renderer import relative_coord
from engine.level_loader import LevelLoader
from engine.song_manager import play_song, load_sound
from engine.GUI.button import Button
from engine.GUI.text import Text
from engine.settings import settings
from engine.visual.vfx import Splash
from engine.GUI.font import font_40
from engine.visual.bloom import Bloom
from engine.visual.auto_exposure import AutoExposure 

_pg.init()
_pg.mixer.init()
_mgl.gc_mode = 'auto'

class Game:
    def __init__(self):
        self.running = True
        self.resolution = (640, 360)
        self.scaledresolution = (1920, 1080)
        self.fps = settings['fps']
        self.path = os.getcwd()
        self.scene = 'main menu'
        self.zoom = 3
        self.scroll = [0, 0]
        self.physics_tickrate = settings['physics tickrate']
        self.simulation = False
        self.white = 0
        self.white_gain = True
        self.last_player = None
        self.last_space = None
        self.transition = False

        self.sounds = {"button hover": load_sound(self.path, 'hover.mp3', settings['sfx volume']), 
                'turret shoot': load_sound(self.path, 'turretshoot.mp3', settings['sfx volume']),
                'splash': load_sound(self.path, 'splash.mp3', settings['sfx volume'])}

        self.spritesheet = load_image(self.path, 'spritesheet.png')

        self.post_processing = True
        
        self.DEBUG_profile = [False, SortKey.TIME]

        self.space = pm.Space()
        self.space.gravity = (0, -900)

        _pg.display.set_caption('FRAGMENTS')
        self.display = _pg.display.set_mode(self.scaledresolution, vsync=1, flags=OPENGL | DOUBLEBUF)

        self.ctx = _mgl.create_context()

        self.ctx.enable(_mgl.BLEND)

        self.program = self.ctx.program(vertex_shader=load_shader(self.path, 'vert.glsl'), fragment_shader=load_shader(self.path, 'frag.glsl'))
        self.program_post_processing = self.ctx.program(vertex_shader=load_shader(self.path, 'vsPostProcessing.glsl'), fragment_shader=load_shader(self.path, 'fsPostProcessing.glsl'))
        self.program_post_processing_effect = self.ctx.program(vertex_shader=load_shader(self.path, 'vsPostProcessing.glsl'), fragment_shader=load_shader(self.path, 'fsPostProcessingFilter.glsl'))
        self.program_objects = self.ctx.program(vertex_shader=load_shader(self.path, 'object.vert.glsl'), fragment_shader=load_shader(self.path, 'object.frag.glsl'))
        self.program_highlights = self.ctx.program(vertex_shader=load_shader(self.path, 'vsHighlights.glsl'), fragment_shader=load_shader(self.path, 'fsHighlights.glsl'))
        self.program_blur = self.ctx.program(vertex_shader=load_shader(self.path, 'vsHighlights.glsl'), fragment_shader=load_shader(self.path, 'blur.glsl'))
        self.program_laser = self.ctx.program(vertex_shader=load_shader(self.path, 'vsLaser.glsl'), fragment_shader=load_shader(self.path, 'fsLaser.glsl'))

        self.programs = [
            self.program,
            self.program_post_processing,
            self.program_objects,
            self.program_highlights,
            self.program_blur,
            self.program_laser
        ]

        self.level_loader = LevelLoader(self.resolution, self.programs, self.path)

        self._mgl_images = load_images_mgl(self.ctx)

        self.clock = _pg.time.Clock()

        self.objects = []
        self.lights = []
    
        self.world_texture = self.ctx.texture(self.scaledresolution, 3, dtype='f2')
        self.world_texture.filter = (_mgl.NEAREST, _mgl.NEAREST)
        self.world_fbo = self.ctx.framebuffer(self.world_texture)

        self.screen_texture = self.ctx.texture(self.scaledresolution, 3, dtype='f1')
        self.screen_texture.filter = (_mgl.NEAREST, _mgl.NEAREST)
        self.screen_fbo = self.ctx.framebuffer(self.screen_texture)
        self.screen_renderer = create_render_object(self.ctx, self.program_post_processing, create_buffer_rect(_pg.Rect(0, 0, self.resolution[0], self.resolution[1]), self.resolution, self.ctx))
        self.screen_renderer_effect = create_render_object(self.ctx, self.program_post_processing_effect, create_buffer_rect(_pg.Rect(0, 0, self.resolution[0], self.resolution[1]), self.resolution, self.ctx))
        self.screen_texture.repeat_x = False
        self.screen_texture.repeat_y = False

        self.background_render = create_render_object(self.ctx, self.program_objects, create_buffer_rect(_pg.Rect(0, 0, *self.resolution), self.resolution, self.ctx), surface_to_texture(load_image(self.path, 'background.png'), self.ctx))

        self.mouse_pos_relative = (0, 0)

        self.vfx = []
        self.bloom = Bloom(self.ctx, self.path, self.scaledresolution, 30)
        self.auto_exposure = AutoExposure(self.ctx, self.path)

        _pg.event.set_blocked([MOUSEMOTION, AUDIODEVICEADDED, ACTIVEEVENT, VIDEOEXPOSE, WINDOWEXPOSED, WINDOWSHOWN, WINDOWFOCUSGAINED, TEXTEDITING
        , JOYBUTTONDOWN, JOYBUTTONUP, JOYHATMOTION, JOYAXISMOTION])

    def left_water(self, arbiter, space, data):
        arbiter.shapes[0].body.origin.touching_water -= 1
    
    def update_light(self):
        self.program_objects['num_lights'] = len(self.lights)
        #self.program_objects['time'] = _pg.mouse.get_pos()[0]

        for i, light in enumerate(self.lights):
            self.program_objects[f'lights[{i}].pos'] = light[0]
            self.program_objects[f'lights[{i}].color'] = light[1]

    def emit_light(self, position: tuple, color: tuple):
        if len(self.lights) < 50:
            light_pos = relative_coord(position, self.resolution, self.ctx)

            light = [light_pos, color]

            self.lights.append(light)

            return light
    
        return False

    def remove_light(self, light):
        try:
            self.lights.remove(light)

        except ValueError:
            print(f'{light} doesnt exist in lights')

    @property
    def mouse_pos(self):
        return (_pg.mouse.get_pos()[0] * self.resolution[0] / self.scaledresolution[0], _pg.mouse.get_pos()[1] * self.resolution[1] / self.scaledresolution[1])

    def open_level(self, name: str):
        self.level_data, self.instances, self.tex_array, self.instances_amount = self.level_loader.load_level(name)

        for block in self.level_data:
            block.init(self.ctx, self.program_objects, self.resolution, self.space)
            if block.light:
                self.emit_light(*block.light)
            block.add(self.objects)

    def render_instanced_objects(self):
        self.program_objects['instanced'] = True

        self.tex_array.use(1)
        self.program_objects['tex_array'] = 1

        self.instances.render(mgl.TRIANGLE_STRIP, instances=self.instances_amount)                    

        self.program_objects['instanced'] = False

    def render_objects(self):
        for object in self.objects:
            if not object.instanced:
                object.render()

            if not object.static:
                object.default_update(self)
        
        self.program_objects['shininess'] = 1

    def render_background(self):
        self.program_objects['ambient_light'] = (0.2, 0.2, 0.2)

        self.program_objects['camera'].write(glm.mat4())
        self.program_objects['num_lights'] = 0
        self.program_objects['z'] = 0

        self.background_render.render()

        self.program_objects['num_lights'] = len(self.lights)
        self.program_objects['camera'].write(self.camera)
        self.program_objects['ambient_light'] = (0.4, 0.4, 0.4)

    def camera_matrix(self):
        eye = glm.vec3(-self.scroll_conversion[0], -self.scroll_conversion[1], self.zoom)
        proj = glm.perspective(1, 1, 0.1, 10.0)
        look = glm.lookAt(eye, (-self.scroll_conversion[0], -self.scroll_conversion[1], 0.0), (0.0, 1, 0.0))
        
        self.camera = glm.mat4(proj * look)

    def update_scroll(self):
        if self.scene == 'main menu':
            target_scroll_x = 0
            target_scroll_y = 0
            
        elif self.scene == 'play':
            target_scroll_x = self.player.rect.x * -1 + self.resolution[0] / 2 - 15
            target_scroll_y = self.player.rect.y * -1 + self.resolution[1] / 2 - 15

        self.scroll[0] += (target_scroll_x - self.scroll[0]) * (2*self.dt)
        self.scroll[1] += (target_scroll_y - self.scroll[1]) * (2*self.dt)

        self.scroll_conversion = self.scroll[0] / self.resolution[0] * 2, -self.scroll[1] / self.resolution[1] * 2

    def update_mouse_pos(self):

        self.mouse_pos_relative = [*self.mouse_pos]

        self.mouse_pos_relative[0] = (((self.mouse_pos_relative[0]-self.resolution[0]/2) / self.zoom) + self.resolution[0]/2 - self.scroll[0])
        self.mouse_pos_relative[1] = (((self.mouse_pos_relative[1]-self.resolution[1]/2) / self.zoom) + self.resolution[1]/2 - self.scroll[1])

    def clear_all_objects(self):
        for obj in self.objects:
            obj.clear()
        
    def init_all_objects(self):
        for obj in self.objects:
            obj.init(self.ctx, self.program_objects, self.resolution, self.space)
    
    def stop_physics_bodies(self):
        for obj in self.objects + [self.player]:
            if obj.physics:
                obj.velocity = (0, 0)

    def get_physics_bodies(self):
        bodies = []
        
        for obj in self.objects + [self.player]:
            if obj.physics:
                bodies.append([(obj.physics_body[0].position, obj.physics_body[0].angle, obj.physics_body[0].velocity), obj])

        self.stop_physics_bodies()

        return bodies

    def set_physics_bodies(self, bodies):
        for body in bodies:
            if body[1].physics:
                body[1].physics_body[0].position, body[1].physics_body[0].angle, body[1].physics_body[0].velocity = body[0]

    def render_screen(self):
        self.world_texture.use()
        self.bloom.highlights_fbo.clear()
        self.bloom.highlights_fbo.use()
        self.bloom.highlights_vao.render(mgl.TRIANGLE_STRIP)

        self.bloom.mips[0].tex = self.bloom.highlights_fbo.color_attachments[0]

        for level in range(self.bloom.levels):
            if not level == self.bloom.levels - 1:
                self.bloom.mips[level].tex.use()
                self.bloom.mips[level+1].fbo.clear()
                self.bloom.mips[level+1].fbo.use()
                self.bloom.mips[level+1].vao.render(mgl.TRIANGLE_STRIP)

        self.bloom.program_mix['tex2'] = 1

        for level in range(self.bloom.levels):
            level = (self.bloom.levels - 1) - level

            if level > 0:
                self.bloom.mips[level - 1].fbo.use()
                self.bloom.mips[level - 1].fbo.color_attachments[0].use(1)
                self.bloom.mips[level].fbo.color_attachments[0].use(0)
                self.bloom.mips[level].mix_vao.render(mgl.TRIANGLE_STRIP)

        self.ctx.screen.use()

        self.world_texture.use(0)
        self.bloom.mips[1].tex.use(1)

        if self.transition:
            if self.white_gain:
                self.white *= 3 ** self.dt

                self.space.gravity = (0, -self.white * 300)
            
                if self.white > 1.5:
                    self.space.gravity = (0, -900)
                    self.simulation = False
                    self.white_gain = False
                    self.set_physics_bodies(self.last_physics_bodies)
                    self.player.set_rect_physics_pos()
                    self.scroll = [self.player.rect.x * -1 + self.resolution[0] / 2 - 15, self.player.rect.y * -1 + self.resolution[1] / 2 - 15]

            else:
                self.white /= 1.7 ** self.dt

                if self.white <= 0.01:
                    self.transition = False
                    self.white = 0

        self.white = max(self.white, 0)

        if self.simulation:         
            self.program_post_processing_effect['white'] = self.white
            self.program_post_processing_effect['tex2'] = 1
            self.screen_renderer_effect.render()
            
        else:
            self.program_post_processing['white'] = self.white
            self.program_post_processing['tex2'] = 1
            self.screen_renderer.render()

    def toggle_simulation(self, v):

        if v:
            self.space.gravity = (0, 0)
            self.white = 2
            self.white_gain = False
            self.simulation = v
            self.last_physics_bodies = self.get_physics_bodies()

        else:
            self.white_gain = True
            self.white = 0.001

        self.transition = True

    def run(self):
        self.screen_light = self.emit_light((50, 50), (1, 1, 1))

        self.player = Player(220, 350)
        self.player.init(self.ctx, self.program_objects, self.resolution, self.space, self.programs)

        self.dt = 1

        self.open_level('map3.tmx')

        self.play_button = Button(self.ctx, self.resolution, self.program_objects, (0, 0), 'Play', self.sounds['button hover'])
        self.play_button.init()
        self.play_button.rect.center = (self.resolution[0]/2, 200)
        self.play_button.update_text()

        self.text = Text(self.ctx, self.program_objects, (100, 350), 'BLOOM TEST', font_40, (255, 255, 255))
        self.text.init(self.resolution)

        self.exit_button = Button(self.ctx, self.resolution, self.program_objects, (0, 0), 'Exit', self.sounds['button hover'])
        self.exit_button.init()
        self.exit_button.rect.center = (self.resolution[0]/2, 250)
        self.exit_button.update_text()

        self.live = 0

        play_song(self.path, 'main_menu.mp3', -1, settings['music volume'])

        exposure = 1

        self.seconds_passed = 0

        self.intensity = 1

        while self.running:
            self.dt = self.clock.tick(self.fps) * 0.001
            self.dt = min(self.dt, 1/30)



            self.seconds_passed += self.dt

            self.program_objects['exposure'] = exposure
            self.program_laser['time'] = self.seconds_passed
            #self.program_post_processing['time'] = self.seconds_passed

            for event in _pg.event.get():
                if event.type == QUIT:
                    self.running = False

                if event.type == KEYDOWN:
                    if event.key == _pg.K_ESCAPE:
                        self.running = False

                    if event.key == K_F12:
                        _pg.display.toggle_fullscreen()

                    if event.key == keybinds['jump'] and self.scene == 'play':
                        self.player.jump()

                    if event.key == _pg.K_e:
                        self.post_processing = not self.post_processing

                    if event.key == _pg.K_q:
                        self.toggle_simulation(True)

                    if event.key == _pg.K_z:
                        self.toggle_simulation(False)

                if event.type == MOUSEWHEEL:
                    self.zoom += event.y/10

                if event.type == MOUSEBUTTONUP:
                    if self.scene == 'main menu':
                        if self.play_button.update(self.mouse_pos):
                            self.scene = 'play'
                            self.remove_light(self.screen_light)

                        elif self.exit_button.update(self.mouse_pos):
                            self.running = False

                if event.type == MOUSEBUTTONDOWN:
                    if self.scene == 'play':
                        pass

            self.update_scroll()
            self.update_mouse_pos()

            #ALL RENDERING MUST GO AFTER THIS LINE 
            #shut up 

            if self.post_processing:
                self.world_fbo.use()
            else:

                self.ctx.screen.use()

            self.camera_matrix()

            self.update_light()

            self.render_background()

            self.program_post_processing['time'] = time.time() % 1

            if self.scene == 'play':
                self.keys = pg.key.get_pressed()

                if self.keys[pg.K_RIGHT]:
                    self.intensity += self.dt

                if self.keys[pg.K_LEFT]:
                    self.intensity -= self.dt

                self.program_post_processing['intensity'] = self.intensity

                if not (self.keys[keybinds['right']] and self.keys[keybinds['left']]):
                    if self.keys[keybinds['left']] and self.player.physics_body[0].velocity[0] > -200:
                        self.player.physics_body[0].apply_force_at_local_point((-50000, 0))
                        self.player.physics_body[1].friction = 0.25

                    elif self.keys[keybinds['right']] and self.player.physics_body[0].velocity[0] < 200:
                        self.player.physics_body[0].apply_force_at_local_point((50000, 0))
                        self.player.physics_body[1].friction = 0.25

                    else:
                        self.player.physics_body[1].friction = 2

                self.player.physics_body[0].angle = 0
                self.player.physics_body[0].moment = float('inf')

                self.space.step(self.dt)

                self.program_objects['set_color'] = True
                self.program_objects['set_color_as'] = (3, 3, 5, 1)
                
                self.text.render()
                self.program_objects['set_color'] = False

                for vfx in self.vfx:
                    vfx.update(self.vfx)
                    vfx.render()

                self.ctx.line_width = 5

                self.player.update(self)
                self.player.render()

                self.render_instanced_objects()

                self.render_objects()

            elif self.scene == 'main menu':
                self.play_button.render(self.mouse_pos)
                self.exit_button.render(self.mouse_pos)

            elif self.scene == 'editor':
                for object in self.objects:
                    object.render()
    
            if self.post_processing:
                self.render_screen()
                #self.auto_exposure.draw(self.ctx.screen.color_attachments[0])

            _pg.display.flip()

        print(self.clock.get_fps())

        self.running = False

if __name__ == '__main__':
    with Profile() as profile:
        game = Game()
        game.run()
        (
        Stats(profile)
        .strip_dirs()
        .sort_stats(game.DEBUG_profile[1])
        .print_stats() if game.DEBUG_profile[0] else None
        )
        #if program crashes, threads will be stopped
        game.running = False