#version 330 

uniform sampler2D tex;
uniform sampler2D texBlur;

uniform float white;

in vec2 uvs;
out vec4 f_color;

vec3 aces(vec3 x) {
  const float a = 2.51;
  const float b = 0.03;
  const float c = 2.43;
  const float d = 0.59;
  const float e = 0.14;
  return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

void main()
{
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec3 color = texture(tex, coords).rgb;
    
    float rr = .3;
    float rg = .769;
    float rb = .189;
    float ra = 0.0;
    
    float gr = .3;
    float gg = .686;
    float gb = .168;
    float ga = 0.0;
    
    float br = .272;
    float bg = .534;
    float bb = .131;
    float ba = 0.0;
    
    float red = (rr * color.r) + (rb * color.b) + (rg * color.g);
    float green = (gr * color.r) + (gb * color.b) + (gg * color.g);
    float blue = (br * color.r) + (bb * color.b) + (bg * color.g);
    
    color = vec3(red,green,blue);
    
    f_color = vec4(color + white, 1);
} 
