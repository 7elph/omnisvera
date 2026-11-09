"""Import supplied sheets intact and derive AtlasTexture rectangles from alpha."""
import argparse
import hashlib
import json
import shutil
import statistics
from functools import lru_cache
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=8)
def row_boundaries(path, rows):
    """The supplied rows are not equally spaced: isolate actual ink bands."""
    with Image.open(path) as image:
        width, height = image.size
        alpha = image.getchannel('A')
        bands = []
        for y in range(height):
            pixels = alpha.crop((0, y, width, y + 1)).get_flattened_data()
            if sum(value >= 64 for value in pixels) < 8:
                continue
            if not bands or y - bands[-1][1] > 8:
                bands.append([y, y + 1])
            else:
                bands[-1][1] = y + 1
        if len(bands) != rows:
            raise ValueError(f'Expected {rows} occupied animation rows, found {len(bands)}')
        return [0] + [(a[1] + b[0]) // 2 for a, b in zip(bands, bands[1:])] + [height]


def frames(path, columns, rows, row):
    with Image.open(path) as image:
        if image.mode != 'RGBA':
            raise ValueError('Dorn must retain RGBA transparency')
        width, height = image.size
        result = []
        for column in range(columns):
            boundaries = row_boundaries(path, rows)
            left, top = round(column * width / columns), boundaries[row]
            right, bottom = round((column + 1) * width / columns), boundaries[row + 1]
            alpha = image.getchannel('A').crop((left, top, right, bottom))
            box = alpha.point(lambda value: 255 if value >= 32 else 0).getbbox()
            if box is None:
                raise ValueError(f'Missing frame {row}/{column}')
            x, y, end_x, end_y = box
            result.append([left + x, top + y, end_x - x, end_y - y])
        return result


def landmarks(image, rect):
    """Calibrate the opaque body/soles, excluding the cyan spell aura."""
    x, y, width, height = rect
    crop = image.crop((x, y, x + width, y + height))
    bronze_rows, solid_rows, solid = {}, {}, []
    for index, (red, green, blue, alpha) in enumerate(crop.get_flattened_data()):
        if alpha < 192:
            continue
        px, py = index % width, index // width
        if red > 50 and red > green * 1.04 and green > blue * 1.06:
            bronze_rows[py] = bronze_rows.get(py, 0) + 1
        if not (blue > red * 1.3 and green > red * 1.3 and blue > 70):
            solid_rows[py] = solid_rows.get(py, 0) + 1
            solid.append((px, py))
    top = min(py for py, count in bronze_rows.items() if count >= 6)
    ground = max(py for py, count in solid_rows.items() if count >= 6) + 1
    feet = [px for px, py in solid if ground - (ground - top) * .12 <= py < ground]
    return {'pivot': [(min(feet) + max(feet)) / 2, ground], 'body_top': top,
            'body_height': ground - top}


def calibrate(manifest, target):
    reference = None
    for name, animation in manifest['animations'].items():
        with Image.open(target / animation['sheet']) as image:
            calibration = [landmarks(image, rect) for rect in animation['frames']]
        body = statistics.median(frame['body_height'] for frame in calibration)
        if name == 'idle':
            reference = body
        animation['calibration'] = calibration
        animation['render_scale'] = round(.52 * reference / body, 8)
    manifest['schema_version'] = 2
    manifest['calibration_method'] = 'opaque_soles_bronze_body_v1'
    return manifest


def recalibrate_existing():
    target = PROJECT / 'assets/sprites'
    manifest = json.loads((target / 'dorn.json').read_text(encoding='utf-8'))
    for name, source in manifest['sources'].items():
        if hashlib.sha256((target / name).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Original image changed: review before recalibration')
    for row, name in enumerate(['idle', 'walk_down', 'walk_up', 'walk_left', 'walk_right']):
        manifest['animations'][name]['frames'] = frames(target / 'dorn-motion.png', 8, 5, row)
    manifest = calibrate(manifest, target)
    (target / 'dorn.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Recalibrated frame regions, body scale and sole pivots; original PNGs unchanged')


def import_assets(source):
    target = PROJECT / 'assets/sprites'
    target.mkdir(parents=True, exist_ok=True)
    files = [('07_05_15', 'dorn-motion.png'), ('07_04_55', 'dorn-guard.png'),
             ('07_05_03', 'dorn-cast.png')]
    sources = {}
    for marker, name in files:
        matches = list(source.glob(f'*{marker}.png'))
        if len(matches) != 1:
            raise ValueError(f'Expected one original for {marker}')
        shutil.copyfile(matches[0], target / name)
        sources[name] = {'original': matches[0].name,
                         'sha256': hashlib.sha256(matches[0].read_bytes()).hexdigest()}
    animations = {}
    for row, name in enumerate(['idle', 'walk_down', 'walk_up', 'walk_left', 'walk_right']):
        animations[name] = {'sheet': 'dorn-motion.png', 'fps': 5 if row == 0 else 8,
                            'loop': True, 'frames': frames(target / 'dorn-motion.png', 8, 5, row)}
    animations['guard'] = {'sheet': 'dorn-guard.png', 'fps': 8, 'loop': False,
                           'frames': frames(target / 'dorn-guard.png', 8, 1, 0)}
    animations['cast'] = {'sheet': 'dorn-cast.png', 'fps': 8, 'loop': False,
                          'frames': frames(target / 'dorn-cast.png', 4, 2, 0) +
                                    frames(target / 'dorn-cast.png', 4, 2, 1)}
    manifest = {'schema_version': 1, 'sources': sources, 'pivot': 'bottom_center',
                'direction_policy': 'explicit_supplied_rows', 'animations': animations}
    manifest = calibrate(manifest, target)
    (target / 'dorn.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Imported 3 original RGBA sheets, 56 frames, no image resampling')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path, nargs='?')
    parser.add_argument('--recalibrate-existing', action='store_true')
    args = parser.parse_args()
    if args.recalibrate_existing:
        recalibrate_existing()
    elif args.source:
        import_assets(args.source)
    else:
        parser.error('Provide source or --recalibrate-existing')
