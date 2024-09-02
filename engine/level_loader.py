from pytmx import load_pygame
from objects.block_class import *

name_to_type = {
	'cup1': Cup,
	'cratesmall': CrateSmall,
	'crate': Crate,
	'phone': Phone,
	'wall': Metal,
}

def load_level(path, name):
	data = load_pygame(os.path.join(path, 'engine', 'levels', name), pixelalpha=True)

	level_data = []

	print(data.layers)
	object_layer = data.get_layer_by_name('Objects')
	#tile_layer = data.get_layer_by_name('Tiles')

	for obj in object_layer:
		block = name_to_type[obj.name](obj.x, obj.y, obj.width, obj.height)
		level_data.append(block)


	return level_data