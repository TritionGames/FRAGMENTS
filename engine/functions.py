import math

import moderngl as mgl
import pygame as pg

def surface_to_texture(surface, ctx, swizzle = 'RGBA', flip_y = False):
    
    if flip_y:
        surface = pg.transform.flip(surface, flip_x=False, flip_y=True)

    tex = ctx.texture(surface.get_size(), 4)
    tex.filter = (mgl.NEAREST, mgl.NEAREST)
    tex.swizzle = swizzle
    tex.repeat_x, tex.repeat_y = False, False
    tex.write(surface.get_view('2'))
    return tex

def normalize_angle(angle):
    return angle % (2 * math.pi)

# Function to interpolate between two angles
def interpolate_angle(current_angle, target_angle, t):
    # Normalize the angles
    current_angle = normalize_angle(current_angle)
    target_angle = normalize_angle(target_angle)
    
    # Calculate the difference
    delta_angle = target_angle - current_angle
    
    # Normalize the difference to the range [-π, π]
    if delta_angle > math.pi:
        delta_angle -= 2 * math.pi
    elif delta_angle < -math.pi:
        delta_angle += 2 * math.pi
    
    # Interpolate the angle
    interpolated_angle = current_angle + delta_angle * t
    
    # Normalize the result
    return normalize_angle(interpolated_angle)

def physics_pos_to_rect(position, size):
    return position[0] + -1/2*size[0] + 25, -position[1] + -1/2*size[1] + 25