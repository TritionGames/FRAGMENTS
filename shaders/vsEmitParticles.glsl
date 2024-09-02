# version 330

uniform vec2 pos;
uniform vec2 velocity;
uniform vec3 color;

out vec2 out_pos;
out vec2 out_vel;
out vec3 out_color;

void main() {
    out_pos = pos;
    out_vel = velocity;
    out_color = color;
}