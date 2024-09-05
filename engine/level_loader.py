import moderngl as mgl
from pytmx import load_pygame

from objects.block_class import *
from engine.renderer import create_buffer_rect, relative_coord

name_to_type = {
	'cup1': Cup,
	'cratesmall': CrateSmall,
	'crate': Crate,
	'phone': Phone,
	'wall': Metal,
	'image': Image,
	'lightbulb': Light1
}

def load_level(path, name, programs, resolution):
	data = load_pygame(os.path.join(path, 'engine', 'levels', name), pixelalpha=True)

	level_data = []

	object_layer = data.get_layer_by_name('Objects')
	tile_layer = data.get_layer_by_name('Tileset')

	for obj in object_layer:
		block = eval(obj.type)(obj.x + obj.width/2, obj.y, obj.width, obj.height)

		level_data.append(block)

	ctx = mgl.get_context()

	tex_array = ctx.texture_array((50, 50, len(tuple(tile_layer.tiles()))), 4)
	positions = []

	for i, val in enumerate(tile_layer.tiles()):
		block = Metal(val[0] * 50, val[1] * 50, 50, 50, val[2])
		block.instanced = True

		tex_array.write(surface_to_texture(val[2].convert_alpha(), ctx, 'RGBA').read(), (0, 0, i, 50, 50, 1))

		pos = relative_coord(block.rect.topleft, resolution, ctx)
		positions.append(pos[0])
		positions.append(pos[1])
		positions.append(i)	

		level_data.append(block)

	instance_buffer = ctx.buffer(array('f', positions))
	vao = ctx.vertex_array(programs[2], [(create_buffer_rect(pg.Rect(0, 0, 50, 50), resolution, ctx), '2f 2f', 'vert', 'texcoord'), (instance_buffer, '2f 1f /i', *['in_instance_position', 'image_index'])])

	return level_data, vao, tex_array