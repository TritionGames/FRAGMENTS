#version 330 core

uniform sampler2D tex;
in vec2 uvs;
out vec4 f_color;

uniform float threshold = 0.5;

void main()
{
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec4 color = texture(tex, coords).rgba;

    float brightness = (0.299*color.r + 0.587*color.g + 0.114*color.b);

    vec3 final_color = vec3(0);

    if(brightness > threshold){
        final_color = color.rgb * (brightness - threshold);
    }


    f_color = vec4(final_color, 1);
}
