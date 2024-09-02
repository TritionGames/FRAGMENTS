#version 330 

uniform sampler2D tex;

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

uniform float time;
uniform float white;

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
  float gamma = 0.3f;
  float numColors = 16.0f;

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
    
    mdf *= 1.0; // animate the effect's strength
    
    vec3 col = rgb - noise * mdf;

    return col;
}

uniform float exposure = 1;
uniform int samples = 10;

float warp = 0; // simulate curvature of CRT monitor
float scan = 0; // simulate darkness between scanlines

void main()
{
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec3 color;

    // squared distance from center

    vec2 dc = abs(0.5-coords);
    dc *= dc;
    
    // warp the fragment coordinates
    coords.x -= 0.5; coords.x *= 1.0+(dc.y*(0.3*warp)); coords.x += 0.5;
    coords.y -= 0.5; coords.y *= 1.0+(dc.x*(0.4*warp)); coords.y += 0.5;

    if (coords.y > 1.0 || coords.x < 0.0 || coords.x > 1.0 || coords.y < 0.0){
      discard;
    }

    color = texture(tex, coords).rgb;

    //color = posterize(color);
    
    //vec3 colorBlur = textureBicubic(texBlur, coords).rgb;

    //float brightness = (0.2126*colorBlur.r + 0.7152*colorBlur.g + 0.0722*colorBlur.b);
    
    color *= exposure;
    
    //color += mix(color,vec3(0.0),abs(sin((coords.y)*720)*0.5*scan));

    color = aces(color);

    //color = posterize(color);

    f_color = vec4(color + white, 1);
} 
