import os

def load_shader(path, name):
    file_data = None

    with open(os.path.join(path, 'shaders', name), 'r') as vs_file:
        file_data = vs_file.read()

    return file_data