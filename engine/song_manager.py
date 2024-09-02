import os

import pygame as pg

from engine.settings import settings

pg.mixer.pre_init(44100, -16, 2, 512)
pg.mixer.init()
pg.init()

def play_song(path, name, loops, volume):
    pg.mixer.music.load(os.path.join(path, 'assets', 'music', name))    
    pg.mixer.music.set_volume(volume * settings['master volume'])
    pg.mixer.music.play(loops=loops)

def play_sound(sound):
    channel = pg.mixer.find_channel(force = True)
    channel.play(sound)

def load_sound(path, name, volume):
    sound = pg.mixer.Sound(os.path.join(path, 'assets', 'music', name))
    sound.set_volume(volume * settings['master volume'])

    return sound