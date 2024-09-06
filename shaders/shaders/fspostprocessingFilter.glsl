#version 330 

uniform sampler2D tex;
uniform sampler2D tex2;

in vec2 uvs;
out vec4 f_color;

float rand(vec2 co){
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

vec3 uncharted2Tonemap(vec3 x) {
  float A = 0.15;
  float B = 0.50;
  float C = 0.10;
  float D = 0.20;
  float E = 0.02;
  float F = 0.30;
  float W = 11.2;
  return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F;
}

vec3 uncharted2(vec3 color) {
  const float W = 11.2;
  float exposureBias = 2.0;
  vec3 curr = uncharted2Tonemap(exposureBias * color);
  vec3 whiteScale = 1.0 / uncharted2Tonemap(vec3(W));
  return curr * whiteScale;
}

uniform float time;

uniform vec2 res = vec2(1920, 1080);
uniform float white;

vec3 chromatic_abberation(in sampler2D tex, in vec2 uv){
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


vec3 hueShift( vec3 color, float hueAdjust ){

    const vec3  kRGBToYPrime = vec3 (0.299, 0.587, 0.114);
    const vec3  kRGBToI      = vec3 (0.596, -0.275, -0.321);
    const vec3  kRGBToQ      = vec3 (0.212, -0.523, 0.311);

    const vec3  kYIQToR     = vec3 (1.0, 0.956, 0.621);
    const vec3  kYIQToG     = vec3 (1.0, -0.272, -0.647);
    const vec3  kYIQToB     = vec3 (1.0, -1.107, 1.704);

    float   YPrime  = dot (color, kRGBToYPrime);
    float   I       = dot (color, kRGBToI);
    float   Q       = dot (color, kRGBToQ);
    float   hue     = atan (Q, I);
    float   chroma  = sqrt (I * I + Q * Q);

    hue += hueAdjust;

    Q = chroma * sin (hue);
    I = chroma * cos (hue);

    vec3    yIQ   = vec3 (YPrime, I, Q);

    return vec3( dot (yIQ, kYIQToR), dot (yIQ, kYIQToG), dot (yIQ, kYIQToB) );

}

vec3 hsl2rgb(vec3 c) {
    float t = c.y * ((c.z < 0.5) ? c.z : (1.0 - c.z));
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return (c.z + t) * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), 2.0*t / c.z);
}

vec3 posterize(in vec3 inputColor){
  float gamma = 1.3f;
  float numColors = 4.0f;

  vec3 c = inputColor.rgb;
  c = pow(c, vec3(gamma, gamma, gamma));
  c = c * numColors;
  c = floor(c);
  c = c / numColors;
  c = pow(c, vec3(1.0/gamma));
  
  return c;
}


vec4 cubic(float v){
    vec4 n = vec4(1.0, 2.0, 3.0, 4.0) - v;
    vec4 s = n * n * n;
    float x = s.x;
    float y = s.y - 4.0 * s.x;
    float z = s.z - 4.0 * s.y + 6.0 * s.x;
    float w = 6.0 - x - y - z;
    return vec4(x, y, z, w) * (1.0/6.0);
} 

vec4 textureBicubic(sampler2D sampler, vec2 texCoords){

   vec2 texSize = textureSize(sampler, 0);
   vec2 invTexSize = 1.0 / texSize;
   
   texCoords = texCoords * texSize - 0.5;
   
    vec2 fxy = fract(texCoords);
    texCoords -= fxy;

    vec4 xcubic = cubic(fxy.x);
    vec4 ycubic = cubic(fxy.y);

    vec4 c = texCoords.xxyy + vec2 (-0.5, +1.5).xyxy;
    
    vec4 s = vec4(xcubic.xz + xcubic.yw, ycubic.xz + ycubic.yw);
    vec4 offset = c + vec4 (xcubic.yw, ycubic.yw) / s;
    
    offset *= invTexSize.xxyy;
    
    vec4 sample0 = texture(sampler, offset.xz);
    vec4 sample1 = texture(sampler, offset.yz);
    vec4 sample2 = texture(sampler, offset.xw);
    vec4 sample3 = texture(sampler, offset.yw);

    float sx = s.x / (s.x + s.y);
    float sy = s.z / (s.z + s.w);

    return mix(
       mix(sample3, sample2, sx), mix(sample1, sample0, sx)
    , sy);
}

vec3 filmGrain(vec3 rgb, vec2 uv, float time){
    float mdf = 0.1; // increase for noise amount 
    float noise = (fract(sin(dot(uv+time, vec2(12.9898,78.233)*2.0)) * 43758.5453));
    
    mdf *= 0.5; // animate the effect's strength
    
    vec3 col = rgb - noise * mdf;

    return col;
}

uniform float exposure = 1;
uniform int samples = 10;
uniform float intensity = 1;

vec3 czm_saturation(vec3 rgb, float adjustment)
{
    // Algorithm from Chapter 16 of OpenGL Shading Language
    const vec3 W = vec3(0.2125, 0.7154, 0.0721);
    vec3 intensity = vec3(dot(rgb, W));
    return mix(intensity, rgb, adjustment);
}

vec3 sepia(vec3 color){
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
    
    return vec3(red,green,blue);
}

void main()
{
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec3 color;

    if (coords.y > 1.0 || coords.x < 0.0 || coords.x > 1.0 || coords.y < 0.0){
      discard;
    }

    color = texture(tex, coords).rgb;

    vec4 bloom = texture(tex2, coords);

    color += bloom.rgb * 0.1;

    //vec3 colorBlur = textureBicubic(texBlur, coords).rgb;

    //float brightness = (0.2126*colorBlur.r + 0.7152*colorBlur.g + 0.0722*colorBlur.b);
    
    color *= intensity;
    
    //color += mix(color,vec3(0.0),abs(sin((coords.y)*720)*0.5*scan));

    color = uncharted2(color);

    color = czm_saturation(color, 1.2);

    color.rgb = filmGrain(color.rgb, vec2(uvs.x, 1 - uvs.y), time);

    color = mix(color, sepia(color), 0.75);

    color = ((color.rgb - 0.5f) * max(1.3f, 0)) + 0.5f;

    f_color = vec4(color + white, 1);
} 
