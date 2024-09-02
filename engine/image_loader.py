import os
import pygame as pg

from engine.functions import surface_to_texture

def load_image(path, img):
    return pg.image.load(os.path.join(path, 'assets', 'images', img))

images = {}

for image in os.listdir(os.path.join(os.getcwd(), 'assets', 'images')):
    if image.split('.')[1] == 'png':
        images[image.split('.')[0]] = load_image(os.getcwd(), image)

def load_images_mgl(ctx):
    images = {}

    for image in os.listdir(os.path.join(os.getcwd(), 'assets', 'images')):
        if image.split('.')[1] == 'png':
            images[image.split('.')[0]] = surface_to_texture(load_image(os.getcwd(), image), ctx)

    return images