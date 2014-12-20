/* simple.glsl

simple diffuse lighting based on laberts cosine law; see e.g.:
    http://en.wikipedia.org/wiki/Lambertian_reflectance
    http://en.wikipedia.org/wiki/Lambert%27s_cosine_law
*/
---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3  v_pos;
attribute vec3  v_normal;
attribute vec2 v_tc0;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;
uniform mat4 light_mat;
uniform vec4 light_pos;

varying vec4 normal_vec;
varying vec4 vertex_pos;
varying vec4 lightPos;

//void main (void) {
//    //compute vertex position in eye_sapce and normalize normal vector
//    vec4 pos = modelview_mat * vec4(v_pos,1.0);
//    vertex_pos = pos;
//    lightPos = modelview_mat*light_pos;
//    normal_vec = vec4(v_normal,0.0);
//    texCoord = v_tc0;
//    gl_Position = projection_mat * pos;
//}

uniform vec4 lpos;
uniform vec3 axis;
uniform int angle;
varying vec3 lightVec;
varying vec3 eyeVec;
varying vec3 diffLight;
varying vec2 texCoord;
varying float distSqr;

const float PI = 3.14159265358979323846;

vec3 tangent(vec3 normal) {

     vec3 c1 = cross(normal, vec3(1.0, 0.0, 0.0));
     vec3 c2 = cross(normal, vec3(0.0, 1.0, 0.0));
     
     if (length(c1) > length(c2)) {
      	return normalize(c1);
     }
     return normalize(c2);

}

mat3 rodrigue(int angle, vec3 axis) {

     mat3 A = mat3(
        0., axis.z, -axis.y, // first column (not row!)
   	-axis.z, 0., axis.x, // second column
	-axis.y, axis.x, 0.  // third column
	);
	mat3 Asq = A*A;
	return mat3(1.0) + A * sin(float(angle)/90.*PI) + Asq*(1.-cos(float(angle)/90.*PI));
}

void main() {

     //compute vertex position in eye_space and normalize normal vector
     vec4 pos = modelview_mat * vec4(v_pos,1.0);
     vertex_pos = pos;
     lightPos = modelview_mat*vec4(light_mat[3]);//light_pos;
//     lightPos = light_pos;
//     normal_vec = vec4(v_normal,0.0);
     texCoord = v_tc0;

     vec3 n = normalize(gl_NormalMatrix * v_normal);
     vec3 t = tangent(n);
     vec3 b = cross(n,t);

     vec3 tmpVec = vec3(lightPos.xyz) - vec3(pos.xyz);

     distSqr = length(tmpVec);

     mat3 rotmat = mat3(t, b, n);

     lightVec = rotmat * normalize(tmpVec);

     tmpVec = vec3(-pos.xyz);

     eyeVec = rotmat * normalize(tmpVec);

     diffLight = vec3(.0, .0, 1.);//vec3(gl_ModelViewMatrix * vec4(.0, .0, 1., 1.));

     gl_Position = projection_mat * pos;
}


---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

// varying vec4 normal_vec;
// varying vec4 vertex_pos;
// varying vec4 lightPos;

// uniform mat4 normal_mat;
// uniform sampler2D diffuse;
// varying vec2 texCoord;

// void main (void){
//     //correct normal, and compute light vector (assume light at the eye)
// //    vec4 v_normal = normalize( normal_mat * normal_vec ) ;
//     //reflectance based on lamberts law of cosine
// //    float theta = clamp(dot(v_normal,normalize(lightPos-vertex_pos)), 0.0, 1.0);
//     gl_FragColor = vec4(texture2D(diffuse,texCoord));
// }

varying vec3 lightVec;
varying vec3 eyeVec;
varying vec3 diffLight;
varying vec2 texCoord;
varying float distSqr;
uniform sampler2D nmap;
uniform sampler2D diffuse;
uniform sampler2D specular;
uniform sampler2D roughness;
//uniform sampler2D ni;
//uniform float rLetters;
//uniform float rBase;
//uniform float sLetters;
//uniform float sBase;

const float PI = 3.14159265358979323846;


float chi(float val) {

      if (val > 0.0) {
      	 return 1.0;
      }
      return 0.0;

}

float G(float alpha, vec3 normal, vec3 light, vec3 view, vec3 h) {
      float alpha2 = alpha;//alpha * alpha;
      float costhetah = max(dot(view,h), 0.0);
      float costhetav = max(dot(view,normal), 0.0);
      float thetav = acos(costhetav);
      float G1o = 0.0;
      if (chi(costhetah/costhetav) == 1.0) {
      	 //G1o = 2.0/(1.0+sqrt(1.0+alpha2 * pow(tan(thetav), 2.0)));
	 G1o = 2.0 * costhetav/(costhetav + sqrt(alpha2 + (1.0-alpha2) * costhetav));
      }
      
      costhetah = dot(light, h);
      costhetav = dot(light, normal);
      thetav = acos(costhetav);
      float G1i = 0.0;
      if (chi(costhetah/costhetav) == 1.0) {
      	 //G1i = 2.0/(1.0+sqrt(1.0+alpha2 * pow(tan(thetav), 2.0)));
	 G1i = 2.0 * costhetav/(costhetav + sqrt(alpha2 + (1.0-alpha2) * costhetav));
      }

      return G1i * G1o;

}

float D(float alpha, vec3 normal, vec3 h) {

      float alpha2 = alpha * alpha;
      float costhetah = dot(normal, h);
      float thetah = acos(costhetah);
      
      if (chi(costhetah) == 1.0) {
//      	 return alpha2/(PI * pow(costhetah,4.0)* pow(alpha2 + tan(thetah) * tan(thetah), 2.0));
		 return alpha2/(PI * pow(pow(costhetah, 2.0) * (alpha2-1.0) + 1.0, 2.0));
      }
      else {
      	   return 0.0;
      }
}

float G1V(float dotNV, float k)
{
	return 1.0f/(dotNV*(1.0f-k)+k);
}

vec4 LightingFuncGGX_REF(vec3 N, vec3 V, vec3 L, float roughness, vec3 F0)
{
	float alpha = roughness*roughness;

	vec3 H = normalize(V+L);

	float dotNL = clamp(dot(N,L), 0.0, 1.0);
	float dotNV = clamp(dot(N,V), 0.0, 1.0);
	float dotNH = clamp(dot(N,H), 0.0, 1.0);
	float dotLH = clamp(dot(L,H), 0.0, 1.0);

	float D, vis;
	vec3 F;

	// D
	float alphaSqr = alpha*alpha;
	float pi = 3.14159f;
	float denom = dotNH * dotNH *(alphaSqr-1.0) + 1.0;
	D = alphaSqr/(pi * denom * denom);

	// F
	float dotLH5 = pow(1.0f-dotLH,5.0);
	F = F0 + (vec3(1.0)-F0)*vec3(dotLH5);

	// V
	float k = alpha/2.0f;
	vis = G1V(dotNL,k)*G1V(dotNV,k);

	vec4 specular = vec4(dotNL * D * F * F0 * vis, 1.0);
	return specular;
}

// void main() {

//      vec3 s = pow(texture2D(specular, texCoord).xyz, vec3(2.2));
//      vec3 d = pow(texture2D(diffuse, texCoord).xyz, vec3(2.2));

//      float x = 0./90.;
//      float y = 0./90.;
// //     vec3 lVec = normalize(vec3(x, y, sqrt(1.0-(x*x + y*y))));

//      vec3 lVec = normalize(lightVec);
//      vec3 vVec = normalize(eyeVec);
//      vec3 normal = normalize(texture2D(nmap, texCoord).xyz * 2.0 - 1.0);
//      vec3 nn = normal;//normalize(texture2D(ni, texCoord).xyz * 2.0 - 1.0);
//      float alpha = texture2D(roughness, texCoord).r * rScale;

//      vec4 spec = LightingFuncGGX_REF(normal, vVec, lVec, alpha, s);
// //     gl_FragColor = pow(spec, vec4(1.0/2.2));
//      gl_FragColor = pow((vec4(d * max(dot(lVec, nn), 0.0), 1.0) + spec * sScale)/2.0, vec4(1.0/2.2));
     
// } 

void main() {

//     float distSqr = dot(lightVec, lightVec);
       float x =-45./90.;
       float y = 0./90.;
     vec3 lVec = normalize(lightVec);//normalize(vec3(x, y, sqrt(1.0-(x*x + y*y))));//normalize(vec3(cos(-PI/2.0 - 0.0873), 0.0, -sin(-PI/2.0-0.0873)));//normalize(lightVec); //* inversesqrt(distSqr);

//     vec3 vVec = normalize(lVec);//vec3(0.0, 0.0, 1.0);//lVec;//normalize(eyeVec);//vec3(0.0, 0.0, 1.0);//lVec;//vec3(0.0, 0.0, 1.0);//normalize(eyeVec);
//vec3 vVec = lVec;
vec3 vVec = normalize(vec3(x, y, sqrt(1.0-(x*x+y*y))));
     vec3 normal = normalize(pow(texture2D(nmap, texCoord).xyz, vec3(1.0)) * 2.0 - 1.0);
     vec3 nn = normalize(pow(texture2D(nmap, texCoord).xyz, vec3(1.0)) * 2.0 - 1.0);
     // if (alpha != .5f)
     // 	alpha = alpha/2.0;
     vec3 h = normalize(lVec + vVec);

     vec4 diff = pow(texture2D(diffuse, texCoord), vec4(2.2));     	
//       vec4 diff = vec4(0.1, 0.0, 0.0, 1.0);
     vec4 spec = pow(texture2D(specular, texCoord), vec4(2.2));//15.;

     float alpha = pow(texture2D(roughness, texCoord).r, 1.0);//*1.2;//1.1;//*9./16.0;//80.;//*2.; //* 2.5; //* 8.0;//*8.0 /4.0;//*8.0/6.0;//* 8.0/6.0;//*8.0; // 20.0;//16.0;//2.0;//2.0;

//vec4 spec = vec4(alpha,alpha,alpha,1);

//     if (diff.xyz == vec3(0.))
//     	spec = vec4(vec3(0.), 1.0);

//     float Fr = (texture2D(ni, texCoord).x + texture2D(ni, texCoord).y + texture2D(ni, texCoord).z)/3.0;

     float eta = (1.0+sqrt(.9))/(1.0-sqrt(.9));

     // if (spec.x < 0.12 && spec.y < 0.12 && spec.z < 0.12) {
     //  	eta = 3.4221;
     // }
     // else {
     //  	  eta = 20.1727;
     // }

     //float R = pow((1.0-eta)/(1.0+eta), 2.0);
//      if (spec.x < .1) {
//      	alpha = alpha * rBase;
//      	spec = spec*sBase;
//     }
//      else {
//      	  alpha = alpha *rLetters;
// //	  diff = vec4(0.0);
//      	  //diff = vec4(0.0, 0.0, 1.0, 1.0);
//      	  spec = spec*sLetters;
//      }

//     spec = vec4(spec.b, spec.b, spec.b, 1.0);
     vec4 R = spec;
     vec4 fresnel = R + (vec4(1.0)-R) * vec4(pow(1.0 - dot(h,vVec), 5.0));
     nn.x = -nn.x;
     nn.y = -nn.y;
     normal.x = -normal.x;
     normal.y = -normal.y;
     spec = spec * 21.0;

     float att = 1.0;//((1.0 + 0.22 * distSqr) * (1.0 + 0.2 * distSqr * distSqr));
//     nn = vec3(0., 0., 1.);
//    normal = nn;
//     normal.x = -normal.x;
//     normal.y = -normal.y;
//     nn == normal;
//       normal = nn;
//nn=normal;
//normal = nn;
     gl_FragColor = pow((diff * max(dot(nn, lVec),0.0) + vec4(vec3(spec.xyz),1.0) * vec4(vec3(D(alpha, normal, h)), 1.0) * vec4(vec3(G(alpha, normal, lVec, vVec, h)), 1.0) * fresnel/vec4(4.0 * abs(dot(vVec, normal)) * vec4(abs(dot(lVec, normal))))), vec4(1.0/2.2));
//gl_FragColor = pow(spec, vec4(1.0/2.2));
//gl_FragColor = pow(spec, vec4(1.0/2.2));
}
