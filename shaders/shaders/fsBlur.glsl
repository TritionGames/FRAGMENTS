#version 330 core

uniform sampler2D tex;
in vec2 uvs;
out vec4 f_color;

uniform float intensity = 5;

void main()
{
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec4 colorBlur = vec4(0);

    for(int i = 1; i < 10; i++){
        colorBlur += textureLod(tex, coords, i).rgba * intensity;
    }
    
    f_color = colorBlur;
}
