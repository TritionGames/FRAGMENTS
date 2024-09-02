#version 330

uniform sampler2DArray tex_array;
uniform sampler2D tex;

in vec3 uvs;
in vec4 in_vert;
in float image_id;
out vec4 f_color;

uniform bool instanced = true;
uniform float time = 1;
uniform vec2 offset;
uniform float offset_scale = 1;
uniform bool center_light = false;
uniform float exposure = 1;
uniform vec3 ambient_light = vec3(0.1, 0.1, 0.1);
uniform float zoom;
uniform vec4 set_color_as;
uniform bool set_color;
uniform vec2 scroll;

struct Light{
    vec2 pos;
    vec3 color;
};

#define max_lights 50
uniform Light lights[max_lights];
uniform int num_lights = 1;

const highp float NOISE_GRANULARITY = 0;

float rand(vec2 n) { 
	return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
}

float noise(vec2 p){
	vec2 ip = floor(p);
	vec2 u = fract(p);
	u = u*u*(3.0-2.0*u);
	
	float res = mix(
		mix(rand(ip),rand(ip+vec2(1.0,0.0)),u.x),
		mix(rand(ip+vec2(0.0,1.0)),rand(ip+vec2(1.0,1.0)),u.x),u.y);
	return res*res;
}

uniform float noise_level = 500;

uniform mat4 camera;

void main()
{
    vec2 coords = uvs.xy + offset;

    coords /= offset_scale;

    vec4 color = vec4(0);
    
    if(!set_color){
        //use texture arrays if instanced
        if(instanced){
            color = texture(tex_array, vec3(coords, image_id));
            
        }
        else{
            color = texture(tex, coords);
        }

        vec3 sum = ambient_light;

        for(int i = 0; i < num_lights; i++){
            vec2 light_pos = vec2(lights[i].pos.x * 16/9, lights[i].pos.y);
            vec2 pixel = vec2(in_vert.x * 16/9, in_vert.y);

            float vd = 1;

            float d = min( length(pixel-light_pos) , vd ) / vd;

            d = pow(d, 0.5);

            vec3 col = color.rgb * lights[i].color * ((1.0-d)*1);

            sum += max(col, 0);
        }

        color.rgb *= sum * exposure;

        float brightness = (0.2126*color.r + 0.7152*color.g + 0.0722*color.b);

        float dither = mix(-NOISE_GRANULARITY, NOISE_GRANULARITY, noise(vec2(in_vert.x, in_vert.y)*noise_level));// * (1-min(brightness/1.5, 1));

        if (brightness+dither>0){
            color.rgb += dither;
        }
    }
    else{
        color = set_color_as;
    }
    f_color = color;
}
