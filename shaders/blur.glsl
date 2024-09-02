#version 330 core
out vec4 f_color;
  
in vec2 uvs;

uniform sampler2D tex;
  
uniform bool horizontal;
uniform float weight[5] = float[] (0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

void main()
{             
    vec2 tex_offset = 1.0 / textureSize(tex, 0); // gets size of single texel
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec3 result = texture(tex, coords).rgb * weight[0]; // current fragment's contribution
    if(horizontal)
    {
        for(int i = 1; i < 5; ++i)
        {
            result += texture(tex, coords + vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
            result += texture(tex, coords - vec2(tex_offset.x * i, 0.0)).rgb * weight[i];
        }
    }
    else
    {
        for(int i = 1; i < 5; ++i)
        {
            result += texture(tex, coords + vec2(0.0, tex_offset.y * i)).rgb * weight[i];
            result += texture(tex, coords - vec2(0.0, tex_offset.y * i)).rgb * weight[i];
        }
    }
    f_color = vec4(result, 1.0);
}