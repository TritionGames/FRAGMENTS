#version 330

layout(points) in;
layout(points, max_vertices = 1) out;

uniform float gravity;
uniform float ft;

in vec2 vs_vel[1];
in vec3 vs_color[1];

out vec2 out_pos;
out vec2 out_vel;
out vec3 out_color;

void main() {
    vec2 pos = gl_in[0].gl_Position.xy;
    vec2 velocity = vs_vel[0];

    if (pos.y > -1.0) {
        vec2 vel = velocity + vec2(0.0, gravity);
        out_pos = pos + vel * ft;
        out_vel = vel;
        out_color = vs_color[0];
        EmitVertex();
        EndPrimitive();
    }
}