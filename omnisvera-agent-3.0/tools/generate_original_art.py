"""Original Companion art via the project's own Flux (Workers AI) provider.

Text-only prompts, no reference images: nothing derived from Rage of Mages assets.
Credentials stay where the backend keeps them; this script never prints them."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT.parent / 'omnisvera-agent' / 'backend'
sys.path.insert(0, str(BACKEND))
from app.cloudflare_provider import FluxKleinProvider, ImageProviderError  # noqa: E402

STYLE = ('hand-painted dark fantasy illustration, isometric three-quarter view, late 1990s classic RPG town screen mood, '
         'warm lantern light against blue dusk, rich textures, crisp silhouettes, no text, no letters, no logos, no watermark')
ART = {
    'city': 'A medieval harbor capital town square called Nimalis seen from above at dusk. Exactly five clear landmarks: '
            'far back center a tall stone city gate tower with an open arch; left foreground a crooked narrow potion shop '
            'with green glowing bottles in its round window and a lantern; center a dwarven armorer shop with an anvil sign, '
            'shields and axes on display and a warm forge glow in the doorway; right a large guild hall with blue banners, '
            'a domed roof and wide open double doors; front center a weathered bronze statue of a robed sage on a pedestal. '
            'Cobblestone plaza connecting all of them, a few market crates, seagulls. ' + STYLE,
    'armorer': 'Interior of a dwarven armorer and weapon shop, a stout bearded dwarf smith with a leather apron behind a heavy '
               'oak counter, racks of swords, axes, helmets and round shields on stone walls, forge embers glowing, '
               'shelves with tools, cozy cramped space. ' + STYLE,
    'potions': 'Interior of a cramped harbor-slum potion shop, shelves full of colorful glass flasks and bottles, a hooded '
               'alchemist woman mixing a green liquid over a small burner, hanging dried herbs, damp wooden beams, '
               'a drowned-flask carved sign. ' + STYLE,
    'guild': 'Interior of an adventurers guild hall and inn, a long polished counter with a friendly half-orc innkeeper, '
             'quest notices pinned on a board, a large fireplace, wooden tables with mugs, stairs to rooms upstairs, '
             'blue banners. ' + STYLE,
}


def main(names):
    target = PROJECT / 'assets' / 'original'
    target.mkdir(parents=True, exist_ok=True)
    log_path = target / 'provenance.json'
    log = json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else {}
    provider = FluxKleinProvider(model='flux-2-klein-9b')
    for name in names or list(ART):
        raw = target / f'{name}.download'
        out = target / f'{name}.jpg'
        try:
            provider.generate(ART[name], raw)
        except ImageProviderError as error:
            print(json.dumps({'name': name, 'ok': False, 'error': str(error)}), flush=True)
            continue
        # The provider may return JPEG bytes whatever the name; store a real JPEG for Godot.
        from PIL import Image
        with Image.open(raw) as picture:
            picture.convert('RGB').save(out, quality=88, optimize=True)
        raw.unlink()
        log[name] = {'file': f'assets/original/{name}.jpg', 'model': '@cf/black-forest-labs/flux-2-klein-9b',
                     'prompt': ART[name], 'references': [], 'generated_at': datetime.now(timezone.utc).isoformat()}
        print(json.dumps({'name': name, 'ok': True, 'bytes': out.stat().st_size}), flush=True)
    log_path.write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
