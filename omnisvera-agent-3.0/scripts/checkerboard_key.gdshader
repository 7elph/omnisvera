shader_type canvas_item;
// Rendering only: the original JPEG remains byte-for-byte unchanged.
void fragment() {
	vec4 pixel = COLOR;
	float low = min(pixel.r, min(pixel.g, pixel.b));
	float high = max(pixel.r, max(pixel.g, pixel.b));
	float neutral = 1.0 - smoothstep(0.08, 0.18, high - low);
	float pale = smoothstep(0.65, 0.78, low);
	COLOR.a = pixel.a * (1.0 - neutral * pale);
}
