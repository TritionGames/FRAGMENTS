#version 330

uniform sampler2D tex;

out vec4 f_color;
in vec2 uvs;

const    float kernel[9] = float[9](
        1.0, 2.0, 1.0,
        2.0, 4.0, 2.0,
        1.0, 2.0, 1.0
    );

float kernelSum = 16.0;

    // Define the offsets for the neighboring pixels
const    vec2 offsets[9] = vec2[9](
        vec2(-1.0,  1.0), // Top-left
        vec2( 0.0,  1.0), // Top-center
        vec2( 1.0,  1.0), // Top-right
        vec2(-1.0,  0.0), // Center-left
        vec2( 0.0,  0.0), // Center-center
        vec2( 1.0,  0.0), // Center-right
        vec2(-1.0, -1.0), // Bottom-left
        vec2( 0.0, -1.0), // Bottom-center
        vec2( 1.0, -1.0)  // Bottom-right
    );

void main(){
    vec2 coords = uvs;

    coords.y = 1 - coords.y;

    vec3 result = vec3(0.0);
    for (int i = 0; i < 9; i++)
    {
        vec2 offset = offsets[i] / textureSize(tex, 0); // Scale by texture size
        result += texture(tex, coords + offset).rgb * kernel[i];
    }

    result /= kernelSum; // Normalize the result

    f_color = vec4(result.xy, 1, 1);
}