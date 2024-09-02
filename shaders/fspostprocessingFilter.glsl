#version 330

uniform sampler2D tex;
in vec2 uvs;
out vec4 f_color;

uniform float time;

vec3 posterize(in vec3 inputColor){
  float gamma = 1.3f;
  float numColors = 8.0f;

  vec3 c = inputColor.rgb;
  c = pow(c, vec3(gamma, gamma, gamma));
  c = c * numColors;
  c = floor(c);
  c = c / numColors;
  c = pow(c, vec3(1.0/gamma));
  
  return c;
}

vec3 chromatic_abberation(in sampler2D tex, in vec2 uv, in float time){
    float amount;


    vec2 texSize = textureSize(tex, 0);
    vec2 invTexSize = 1.0 / texSize;

	amount = pow(amount, 3.0);

	amount *= 5;
	
    vec3 col;
    col.r = texture(tex, vec2(uv.x+amount * invTexSize.x,uv.y) ).r;
    col.g = texture(tex, uv).g;
    col.b = texture(tex, vec2(uv.x-amount * invTexSize.y,uv.y) ).b;

	col *= (1.0 - amount * 0.5);

    return col;
}

vec3 filmGrain(vec3 rgb, vec2 uv, float time){
    float mdf = 0.1; // increase for noise amount 
    float noise = (fract(sin(dot(uv+time, vec2(12.9898,78.233)*2.0)) * 43758.5453));
    
    mdf *= 1.0; // animate the effect's strength
    
    vec3 col = rgb - noise * mdf;

    return col;
}

vec3 sharpen(in vec2 uv, in sampler2D tex){
	vec2 s = 1.0 / textureSize(tex, 0);
	
	vec3 texA = texture(tex, uv + vec2(-s.x, -s.y) * 1.5 ).rgb;
	vec3 texB = texture(tex, uv + vec2( s.x, -s.y) * 1.5 ).rgb;
	vec3 texC = texture(tex, uv + vec2(-s.x,  s.y) * 1.5 ).rgb;
	vec3 texD = texture(tex, uv + vec2( s.x,  s.y) * 1.5 ).rgb;
   
    vec3 around = 0.25 * (texA + texB + texC + texD);
	vec3 center  = texture(tex, uv).rgb;
	
	float sharpness = 3.0;

    return (center - around) * sharpness;
}

vec3 czm_saturation(vec3 rgb, float adjustment)
{
    // Algorithm from Chapter 16 of OpenGL Shading Language
    const vec3 W = vec3(0.2125, 0.7154, 0.0721);
    vec3 intensity = vec3(dot(rgb, W));
    return mix(intensity, rgb, adjustment);
}

void main()
{
    vec4 color = texture(tex, vec2(uvs.x, 1 - uvs.y)).rgba;

    color.rgb = ((color.rgb - 0.5) * max(0.1f, 0)) + 0.5;

    color.rgb += chromatic_abberation(tex, vec2(uvs.x, 1 - uvs.y), time);
    color.rgb /= 2; 

    color.rgb += sharpen(vec2(uvs.x, 1 - uvs.y), tex);
    //color.rgb /= 2;

    color.rgb = czm_saturation(color.rgb, 2);
    color.rgb = filmGrain(color.rgb, vec2(uvs.x, 1 - uvs.y), time);
    color.rgb += posterize(color.rgb);
    color.rgb /= 2;


    f_color = color;
}