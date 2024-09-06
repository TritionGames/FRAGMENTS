import moderngl as mgl
import pygame as pg
from pytmx import load_pygame

from objects.block_class import *
from engine.renderer import create_buffer_rect, relative_coord
from engine.functions import surface_to_texture

class LevelLoader:
	def __init__(self, resolution, programs, path):
		self.cache = {}
		self.resolution = resolution
		self.programs = programs
		self.path = path

	def clear_cache(self, name):
		for level in self.cache[name]:
			for obj in level:
				obj.clear()

		del self.cache[name]

	def load_level(self, name, cache = True):
		if (not name in self.cache) or not cache:
			data = load_pygame(os.path.join(self.path, 'engine', 'levels', name), pixelalpha=True)

			self.level_data = []

			object_layer = data.get_layer_by_name('Objects')
			tile_layer = data.get_layer_by_name('Tileset')

		else:
			self.level_data = self.cache[name]

		object_layer = sorted(object_layer, key = lambda x: x.z)

		for obj in object_layer:
			if obj.type == 'Image':
				block = eval(obj.type)(obj.x, obj.y, obj.width, obj.height, obj.image)

			else:
				block = eval(obj.type)(obj.x, obj.y, obj.width, obj.height)

			if 'brightness' in obj.properties:
				block.brightness = obj.properties['brightness']

			if 'shininess' in obj.properties:
				block.shininess = obj.properties['shininess']

			if 'z' in obj.properties:
				block.z = obj.properties['z']

			self.level_data.append(block)

		self.cache[name] = self.level_data

		self.generate_instanced_tileset(tile_layer)

		return self.level_data, self.vao, self.tex_array, self.instances_count

	def generate_instanced_tileset(self, tile_layer):
		ctx = mgl.get_context()

		self.instances_count = len(tuple(tile_layer.tiles()))
		self.tex_array = ctx.texture_array((50, 50, self.instances_count), 4)
		self.tex_array.filter = (mgl.NEAREST, mgl.NEAREST)
		positions = []

		for i, val in enumerate(tile_layer.tiles()):
			
			block = Metal(val[0] * 50, val[1] * 50, 50, 50, val[2])
			block.instanced = True
			self.tex_array.write(pg.image.tobytes(val[2], 'RGBA'), (0, 0, i, 50, 50, 1))

			pos = relative_coord((val[0] * 50 + self.resolution[0]/2, val[1] * 50 + self.resolution[1]/2), self.resolution, ctx)

			positions.append(pos[0])
			positions.append(pos[1])
			positions.append(i)	

			self.level_data.append(block)

		self.instance_buffer = ctx.buffer(array('f', positions))
		self.vao = ctx.vertex_array(self.programs[2], [(create_buffer_rect(pg.Rect(0, 0, 50, 50), self.resolution, ctx), '2f 2f', 'vert', 'texcoord'), (self.instance_buffer, '2f 1f /i', *['in_instance_position', 'image_index'])])