#version 330

in vec2 vert;
out vec4 coord;

uniform mat4 camera;

uniform vec2 scroll = vec2(0, 0);
uniform float zoom = 1;

void main() {

    gl_Position = camera * vec4(vert, 1, 1.0);
    coord = camera * vec4(vert, 1, 1.0);;
}
