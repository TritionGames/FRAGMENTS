#version 330

uniform sampler2D tex;
in vec2 uv;
out vec4 f_color;

uniform bool flip;


void main()
{
    vec4 color;

    if(flip){
        color = texture(tex, vec2(uv.x, 1 - uv.y)).rgba;
    }
    else{
        color = texture(tex, uv).rgba;
    }

    f_color = vec4(color.rgb, 1);
}
