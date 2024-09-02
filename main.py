import os
import time
import threading
import glm



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
from engine.level_loader import load_level
from engine.song_manager import play_song, load_sound
from engine.GUI.button import Button
from engine.GUI.text import Text
from engine.settings import settings
from engine.visual.vfx import Splash
from engine.GUI.font import font_40

_pg.init()
_pg.mixer.init()
_mgl.gc_mode = 'auto'

class Game:
    def __init__(self):
        self.running = True
        self.resolution = (640, 360)
        self.scaledresolution = (1920, 1079)
        self.fps = settings['fps']
        self.path = os.getcwd()
        self.scene = 'main menu'
        self.zoom = 3
        self.scroll = [0, 0]
        self.physics_tickrate = settings['physics tickrate']

        self.sounds = {"button hover": load_sound(self.path, 'hover.mp3', settings['sfx volume']), 
                'turret shoot': load_sound(self.path, 'turretshoot.mp3', settings['sfx volume']),
                'splash': load_sound(self.path, 'splash.mp3', settings['sfx volume'])}

        self.spritesheet = load_image(self.path, 'spritesheet.png')

        self.post_processing = True
        
        self.DEBUG_profile = [False, SortKey.TIME]

        self.space = pm.Space()
        self.space.gravity = (0, -900)

        _pg.display.set_caption('FRAGMENTS')
        self.display = _pg.display.set_mode(self.scaledresolution, vsync=0, flags=OPENGL | DOUBLEBUF)

        self.ctx = _mgl.create_context()

        self.ctx.enable(_mgl.BLEND)

        self.program = self.ctx.program(vertex_shader=load_shader(self.path, 'vs.glsl'), fragment_shader=load_shader(self.path, 'fs.glsl'))
        self.program_post_processing = self.ctx.program(vertex_shader=load_shader(self.path, 'vsPostProcessing.glsl'), fragment_shader=load_shader(self.path, 'fsPostProcessing.glsl'))
        self.program_texture_array = self.ctx.program(vertex_shader=load_shader(self.path, 'vsArray.glsl'), fragment_shader=load_shader(self.path, 'fsTextureArray.glsl'))
        self.program_highlights = self.ctx.program(vertex_shader=load_shader(self.path, 'vsHighlights.glsl'), fragment_shader=load_shader(self.path, 'fsHighlights.glsl'))
        self.program_blur = self.ctx.program(vertex_shader=load_shader(self.path, 'vsHighlights.glsl'), fragment_shader=load_shader(self.path, 'blur.glsl'))
        self.program_laser = self.ctx.program(vertex_shader=load_shader(self.path, 'vsLaser.glsl'), fragment_shader=load_shader(self.path, 'fsLaser.glsl'))

        self.programs = [
            self.program,
            self.program_post_processing,
            self.program_texture_array,
            self.program_highlights,
            self.program_blur,
            self.program_laser
        ]

        self._mgl_images = load_images_mgl(self.ctx)

        self.clock = _pg.time.Clock()

        self.objects = []
        self.lights = []
    
        self.world_texture = self.ctx.texture(self.scaledresolution, 3, dtype='f1')
        self.world_texture.filter = (_mgl.NEAREST, _mgl.NEAREST)
        self.world_fbo = self.ctx.framebuffer(self.world_texture)

        self.screen_texture = self.ctx.texture(self.scaledresolution, 3, dtype='f1')
        self.screen_texture.filter = (_mgl.NEAREST, _mgl.NEAREST)
        self.screen_fbo = self.ctx.framebuffer(self.screen_texture)
        self.screen_renderer = create_render_object(self.ctx, self.program_post_processing, create_buffer_rect(_pg.Rect(0, 0, self.resolution[0], self.resolution[1]), self.resolution, self.ctx))
        self.screen_texture.repeat_x = False
        self.screen_texture.repeat_y = False

        self.background_render = create_render_object(self.ctx, self.program_texture_array, create_buffer_rect(_pg.Rect(-1000, 0, self.resolution[0]*5, self.resolution[1] * 5), self.resolution, self.ctx), surface_to_texture(load_image(self.path, 'background.png'), self.ctx))
        self.background_render.texture.repeat_x = True
        self.background_render.texture.repeat_y = True

        self.mouse_pos_relative = (0, 0)

        self.vfx = []

        _pg.event.set_blocked([MOUSEMOTION, AUDIODEVICEADDED, ACTIVEEVENT, VIDEOEXPOSE, WINDOWEXPOSED, WINDOWSHOWN, WINDOWFOCUSGAINED, TEXTEDITING
        , JOYBUTTONDOWN, JOYBUTTONUP, JOYHATMOTION, JOYAXISMOTION])

    def splash(self, arbiter, space, data):
        if arbiter.shapes[0].body.origin.touching_water == 0:
            if arbiter.shapes[0].body.velocity.length > 200:
                play_sound(self.sounds['splash'])
                for p in arbiter.contact_point_set.points:
                    self.vfx.append(Splash(physics_pos_to_rect(p.point_a, (50, 50)), self.ctx, self.program_texture_array, self.resolution))
        arbiter.shapes[0].body.origin.touching_water += 1
        return True
    
    def left_water(self, arbiter, space, data):
        arbiter.shapes[0].body.origin.touching_water -= 1
    
    def update_light(self):
        self.program_texture_array['num_lights'] = len(self.lights)
        #self.program_texture_array['time'] = _pg.mouse.get_pos()[0]

        for i, light in enumerate(self.lights):
            self.program_texture_array[f'lights[{i}].pos'] = light[0]
            self.program_texture_array[f'lights[{i}].color'] = light[2]

    def emit_light(self, position: tuple, strength: float, color: tuple):
        if len(self.lights) < 50:
            light_pos = relative_coord(position, self.resolution, self.ctx)

            light = [light_pos, strength, color]

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

    def start_physics(self):
        clock = _pg.time.Clock()

        while self.running:
            clock.tick(self.physics_tickrate)
            physics_dt = 1/self.physics_tickrate * self.physics_tickrate

            #self.player.physics_body[0].position = (self.player.rect.x, -self.player.rect.y)
            try:
                if self.scene == 'play':
                    self.keys = _pg.key.get_pressed()

                        #self.player.velocity[0] /= (10*60) ** dt

                    if not (self.keys[keybinds['right']] and self.keys[keybinds['left']]):
                        if self.keys[keybinds['left']] and self.player.physics_body[0].velocity[0] > -200:
                            self.player.physics_body[0].apply_force_at_local_point((-100000 * physics_dt, 0))
                            self.player.physics_body[1].friction = 0.5

                        elif self.keys[keybinds['right']] and self.player.physics_body[0].velocity[0] < 200:
                            self.player.physics_body[0].apply_force_at_local_point((100000 * physics_dt, 0))
                            self.player.physics_body[1].friction = 0.5

                        else:
                            self.player.physics_body[1].friction = 1.5

                    self.player.physics_body[0].angle = 0
                    self.player.physics_body[0].moment = float('inf')

                    self.space.step(1/self.physics_tickrate)

            except Exception as e:
                print(e)

                break

    def run(self):
        self.screen_light = self.emit_light((50, 50), 0.5, (1, 1, 1))

        self.player = Player(220, 350)
        self.player.init(self.ctx, self.program_texture_array, self.resolution, self.space, self.programs)

        '''for block in load_level(self.path, 'file.lvl'):
            block.init(self.ctx, self.program_texture_array, self.resolution, space=self.space, programs = self.programs)

            if block.light[1]:
                self.emit_light(block.light[0], block.light[1], block.light[2])

            block.add(self.objects)'''

        for block in load_level(self.path, 'MAP1.tmx'):
            block.init(self.ctx, self.program_texture_array, self.resolution, self.space)
            block.add(self.objects)


        self.dt = 0

        #world_render, tex = generate_instances(self.objects, (50, 50), (50, 50), self.program_texture_array, self.ctx, self.resolution, rotate)

        #vao_instanced, texture_array = generate_instances(self.objects, (50, 50), (50, 50), self.program_texture_array, self.ctx, self.resolution)

        #light1 = self.emit_light((400, 100), 0.2, 5, (1, 1, 1))

        self.play_button = Button(self.ctx, self.resolution, self.program_texture_array, (0, 0), 'Play', self.sounds['button hover'])
        self.play_button.init()
        self.play_button.rect.center = (self.resolution[0]/2, 200)
        self.play_button.update_text()

        self.text = Text(self.ctx, self.program_texture_array, (100, 400), 'skbidi biden', font_40, (255, 255, 255))
        self.text.init(self.resolution)

        self.exit_button = Button(self.ctx, self.resolution, self.program_texture_array, (0, 0), 'Exit', self.sounds['button hover'])
        self.exit_button.init()
        self.exit_button.rect.center = (self.resolution[0]/2, 250)
        self.exit_button.update_text()

        self.live = 0

        play_song(self.path, 'main_menu.mp3', -1, settings['music volume'])

        exposure = 1

        threading.Thread(target=self.start_physics).start()

        self.seconds_passed = 0

        while self.running:
            dt = self.clock.tick(self.fps) * 0.001
            dt = min(dt, 1/30)

            self.seconds_passed += dt

            #THIS IS VERY IMPORTANT
            self.dt = dt

            self.program_texture_array['exposure'] = exposure
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

            if self.scene == 'main menu':
                target_scroll_x = 0
                target_scroll_y = 0
                
            #elif self.scene == 'play':
            target_scroll_x = self.player.rect.x * -1 + self.resolution[0] / 2 - 15
            target_scroll_y = self.player.rect.y * -1 + self.resolution[1] / 2 - 15

            self.scroll[0] += (target_scroll_x - self.scroll[0]) * (3*dt)
            self.scroll[1] += (target_scroll_y - self.scroll[1]) * (3*dt)

            self.mouse_pos_relative = [*self.mouse_pos]

            self.mouse_pos_relative[0] = (((self.mouse_pos_relative[0]-self.resolution[0]/2) / self.zoom) + self.resolution[0]/2 - self.scroll[0])
            self.mouse_pos_relative[1] = (((self.mouse_pos_relative[1]-self.resolution[1]/2) / self.zoom) + self.resolution[1]/2 - self.scroll[1])

            scroll_conversion = self.scroll[0] / self.resolution[0] * 2, -self.scroll[1] / self.resolution[1] * 2

            #ALL RENDERING MUST GO AFTER THIS LINE
            if self.post_processing:
                self.world_fbo.use()
            else:
                self.ctx.screen.use()

            #x, y = relative_coord(self.player.rect.center, self.resolution, self.ctx) 
            #self.program_post_processing['time'] = time.time() % 1

            eye = glm.vec3(-scroll_conversion[0], -scroll_conversion[1], self.zoom)
            proj = glm.perspective(1, 1, 0.1, 10.0)
            look = glm.lookAt(eye, (-scroll_conversion[0], -scroll_conversion[1], 0.0), (0.0, 1, 0.0))

            self.ctx.clear()
            #self.ctx.enable(mgl.DEPTH_TEST | mgl.CULL_FACE)

            self.program_texture_array['camera'].write(proj * look)
            self.program_laser['camera'].write(proj * look)

            self.update_light()

            #self.program_texture_array['ambient_light'] = (0.2, 0.2, 0.2)
            self.program_texture_array['instanced'] = False
            #self.program_texture_array['scroll'] = scroll_conversion
            self.program_texture_array['z'] = -2

            self.background_render.render()

            self.program_texture_array['z'] = 1

            #self.camera = self.camera.camera_matrix(1)
            self.splash_handler = self.space.add_collision_handler(2, 3)
            self.splash_handler.begin = self.splash
            self.splash_handler.separate = self.left_water

            self.splash_handler_player = self.space.add_collision_handler(1, 3)
            self.splash_handler_player.begin = self.splash
            self.splash_handler_player.separate = self.left_water

            if self.scene == 'play':

                    #self.space.step(dt/2)

                self.text.render()

                for vfx in self.vfx:
                    vfx.update(self.vfx)
                    vfx.render()

                self.ctx.line_width = 5

                self.player.update(self)
                self.player.render()

                for object in self.objects:
                    object.render()

                    if not object.static:
                        object.default_update(self)

            elif self.scene == 'main menu':
                self.play_button.render(self.mouse_pos)
                self.exit_button.render(self.mouse_pos)

            elif self.scene == 'editor':
                for object in self.objects:
                    object.render()
    
            if self.post_processing:
                self.ctx.screen.use()

                self.world_texture.use(0)

                self.screen_renderer.render()

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