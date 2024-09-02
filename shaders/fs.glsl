#version 330

uniform sampler2D tex;
in vec2 uvs;
out vec4 f_color;

void main()
{
    vec4 color = texture(tex, uvs).rgba;

    f_color = vec4(color.rgb, color.a);
}
