#version 330

in vec2 vert;
in vec2 texcoord;
out vec2 uvs;
out float instance_id;

uniform vec2 scroll = vec2(0, 0);
uniform float zoom = 1;
void main() {
    uvs = texcoord; 

    gl_Position = vec4((vert + scroll) * zoom, 0.0, 1.0);

}
