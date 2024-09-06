#version 330 core

in vec2 vert;
in vec2 texcoord;
in float image_index;
in vec2 in_instance_position;

uniform mat4 camera;
uniform float z = 1;
uniform vec2 position;
uniform bool instanced;

out vec3 uvs;
out vec4 in_vert;
out float image_id;

void main() {
    uvs = vec3(texcoord, z); 

    vec2 pos = vert + position;

    if(instanced){
        pos += in_instance_position;
    }

    gl_Position = camera * vec4(pos, z, 1.0);

    image_id = image_index;
    in_vert = vec4(pos, z, 1.0);
}
