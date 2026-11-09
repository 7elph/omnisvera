"""Keep the supplied JPG intact; derive frames and floor pivots only."""
import argparse
import hashlib
import json
import shutil
import statistics
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]

def import_sheet(source):
    target = PROJECT / 'assets/sprites/morthak-motion.jpg'
    shutil.copy2(source, target)
    animations = {}
    with Image.open(target) as image:
        image = image.convert('RGB')
        width, height = image.size
        occupancy = []
        for y in range(height):
            pixels = image.crop((0, y, width, y+1)).get_flattened_data()
            occupancy.append(sum(min(rgb) < 160 or max(rgb)-min(rgb) > 45 for rgb in pixels))
        boundaries = [0]
        for row in range(1,5):
            nominal = round(row * height / 5)
            window = range(nominal-30, nominal+16)
            minimum = min(occupancy[y] for y in window)
            if minimum > width * .05:
                raise ValueError(f'No safe separation before row {row}')
            boundaries.append(round(statistics.median(y for y in window if occupancy[y] == minimum)))
        boundaries.append(height)
        for row, name in enumerate(['idle', 'walk_down', 'walk_up', 'walk_left', 'walk_right']):
            frames, calibration = [], []
            for column in range(8):
                left, right = round(column * width / 8), round((column + 1) * width / 8)
                top, bottom = boundaries[row:row+2]
                pixels = image.crop((left, top, right, bottom))
                ink, body = [], []
                for index, rgb in enumerate(pixels.get_flattened_data()):
                    x, y = index % pixels.width, index // pixels.width
                    if min(rgb) < 160 or max(rgb) - min(rgb) > 45:
                        ink.append((x, y))
                    if pixels.width * .36 < x < pixels.width * .85 and max(rgb) < 125:
                        body.append((x, y))
                x0, x1 = min(x for x,y in ink), max(x for x,y in ink) + 1
                y0, y1 = min(y for x,y in ink), max(y for x,y in ink) + 1
                ground = max(y for x,y in body) + 1
                feet = [x for x,y in body if y >= ground - 7]
                body_top = min(y for x,y in body)
                frames.append([left + x0, top + y0, x1 - x0, y1 - y0])
                calibration.append({'pivot': [(min(feet) + max(feet)) / 2 - x0, ground - y0],
                                    'body_top': body_top - y0, 'body_height': ground - body_top})
            animations[name] = {'sheet': target.name, 'fps': 5 if row == 0 else 8, 'loop': True,
                'frames': frames, 'calibration': calibration,
                'render_scale': round(93.34 / statistics.median(c['body_height'] for c in calibration), 8)}
    metadata = {'schema_version': 2, 'character_id': 'morthak', 'display_name': 'Morthak',
                'row_boundaries': boundaries,
                'background_filter': 'baked_light_checkerboard', 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'animations': animations}
    target.with_name('morthak.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print('Imported original JPG unchanged; 40 frames, 5 animations, sole pivots')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    import_sheet(parser.parse_args().source)
