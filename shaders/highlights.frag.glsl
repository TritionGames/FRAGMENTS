#version 330

uniform sampler2D tex;
in vec2 uv;
out vec4 f_color;

uniform bool flip;
uniform float threshold = 1;

void main()
{
    vec4 color;

    if(flip){
        color = texture(tex, vec2(uv.x, 1 - uv.y)).rgba;
    }
    else{
        color = texture(tex, uv).rgba;
    }

    float brightness = (0.2126*color.r + 0.7152*color.g + 0.0722*color.b);

    f_color = vec4(color.rgb, max(brightness - threshold, 0));
}
