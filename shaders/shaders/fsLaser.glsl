#version 330

in vec4 coord;
out vec4 f_color;

uniform vec4 color = vec4(1, 1, 1, 1);
uniform float time = 0;

float rand(vec2 co){
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main()
{
    f_color = color/2 + time/1000000;
}
