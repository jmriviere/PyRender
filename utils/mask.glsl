---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3  v_pos;
attribute vec3  v_normal;
attribute vec2 v_tc0;

uniform mat4 projection_mat;
uniform mat4 modelview_mat;

varying vec2 texCoord;

void main(void) {

    texCoord = v_tc0;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 1.0);
    
}

---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

uniform sampler2D tex1;
uniform float threshold;

varying vec2 texCoord;

void main(void) {
    float specG = pow(texture2D(tex1, texCoord).y,2.2);
    float color = 0.0;
    if (specG > threshold) {
        color = 1.0;
    }
    gl_FragColor = vec4(color, color, color, 1.0);
    
}
