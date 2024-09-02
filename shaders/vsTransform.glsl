#version 330

in vec2 in_pos;
in vec2 in_vel;
in vec3 in_color;

out vec2 vs_vel;
out vec3 vs_color;

void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
    vs_vel = in_vel;
    vs_color = in_color;
}