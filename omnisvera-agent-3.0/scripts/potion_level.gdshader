shader_type canvas_item;
// HP potion: the red liquid above the current level turns into dark empty glass.
uniform float level : hint_range(0.0, 1.0) = 1.0;
uniform float liquid_top = 0.45;     // UV y of the full liquid surface
uniform float liquid_bottom = 0.985; // UV y of the bottle floor
uniform float wobble = 0.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float surface = mix(liquid_bottom, liquid_top, clamp(level, 0.0, 1.0));
	surface += sin(UV.x * 18.0 + wobble) * 0.004;
	float redness = clamp((c.r - max(c.g, c.b)) * 2.2, 0.0, 1.0);
	if (UV.y < surface) {
		float grey = dot(c.rgb, vec3(0.3, 0.59, 0.11));
		vec3 empty = vec3(grey * 0.32, grey * 0.30, grey * 0.34);
		c.rgb = mix(c.rgb, empty, redness);
	} else if (UV.y < surface + 0.012 && level > 0.01 && level < 0.99) {
		c.rgb = mix(c.rgb, vec3(1.0, 0.55, 0.45), redness * 0.6);
	}
	COLOR = c;
}
