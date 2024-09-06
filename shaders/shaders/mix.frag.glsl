#version 330

uniform sampler2D tex;
uniform sampler2D tex2;
in vec2 uv;
out vec4 f_color;

uniform bool flip;

void main()
{
    vec3 color;

    color = texture(tex, uv).rgb;

    if(flip){
        color += texture(tex2, vec2(uv.x, 1 - uv.y)).rgb;
    }
    else{
        color += texture(tex2, uv).rgb;
    }

    f_color = vec4(color.rgb, 1);
}
