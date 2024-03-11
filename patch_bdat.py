import json
import sys
import tomllib
import os
import struct
import glob
import argparse
import random

LANG_RES = {
    'gem': {},
    'art': {},
    'accessory': {},
    'affinity': {}
}
BDAT_PATH = ""

def abort(msg, code=1):
    print(msg)
    sys.exit(code)

def murmur32(s):
    """Return the 32-bit Murmur3 hash of s using seed 0."""
    c1 = 0xCC9E2D51
    c2 = 0x1B873593
    c3 = 0x85EBCA6B
    c4 = 0xC2B2AE35
    r1 = 15
    r2 = 13
    s3 = 16
    s4 = 13
    s5 = 16
    m = 5
    n = 0xE6546B64

    s = s.encode('utf-8')
    l = len(s)
    hash = 0
    i = 0
    while i+4 <= l:
        k = struct.unpack('<I', s[i:i+4])[0]
        i += 4
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32-r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        hash ^= k
        hash = ((hash << r2) | (hash >> (32-r2))) & 0xFFFFFFFF
        hash = (hash * m + n) & 0xFFFFFFFF
    if i < l:
        s += b'\0\0\0'
        k = struct.unpack('<I', s[i:i+4])[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32-r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        hash ^= k
    hash ^= l
    hash ^= hash >> s3
    hash = (hash * c3) & 0xFFFFFFFF
    hash ^= hash >> s4
    hash = (hash * c4) & 0xFFFFFFFF
    hash ^= hash >> s5
    return f'<{hash:08X}>'

def get_table(name, file, lang=None):
    assert BDAT_PATH
    path = f"{BDAT_PATH}/{lang}/game/{file}/{name}.json" if lang else f"{BDAT_PATH}/{file}/{name}.json"
    if not os.path.exists(path):
        abort(f"Table file {path} not found")
    with open(path) as f:
        return json.loads(f.read())

def save_table(table, name, file, lang=None):
    assert BDAT_PATH
    path = f"{BDAT_PATH}/{lang}/game/{file}/{name}.json" if lang else f"{BDAT_PATH}/{file}/{name}.json"
    if not os.path.exists(path):
        abort(f"Table file {path} not found, will not create new tables")
    with open(path, 'w') as f:
        return f.write(json.dumps(table, indent=2))

def find_or_create_row(bdat, label, key='label', dup_row=-1):
    """Only creates a new row if it can't find one by label"""
    rows = bdat['rows']
    hash = murmur32(label)
    matching = [i for i in range(len(rows)) if rows[i][key] == hash]
    if matching:
        return rows[matching[0]]
    last_id = 0 if not rows else rows[-1]['$id']
    copy = rows[dup_row].copy()
    copy['$id'] = last_id + 1
    copy[key] = hash
    rows.append(copy)
    return copy

def row_by_id(bdat, id):
    rows = bdat['rows']
    row = next((row for row in rows if row['$id'] == id), None)
    if row: return row
    abort(f"row {id} not found")

def patch_lang(toml, lang):
    table = get_table('msg_item_precious', 'system', lang=lang)
    items = toml['item']

    for itm_type, chrs in items.items():
        for chr, text in chrs.items():
            name = find_or_create_row(table, f"FR_UK_{itm_type}_{chr}")
            name['name'] = text['name']
            caption = find_or_create_row(table, f"FR_UK_{itm_type}_{chr}_cap")
            caption['name'] = text['caption']
            LANG_RES[itm_type][chr] = {
                'name': name['$id'],
                'caption': caption['$id']
            }

    save_table(table, 'msg_item_precious', 'system', lang=lang)

def patch_items(toml):
    items = toml['item']
    cfg = toml['item_config']
    table = get_table('ITM_Precious', 'sys')

    for itm_type, chrs in items.items():
        for chr, id in chrs.items():
            row = row_by_id(table, id)
            row['Name'] = LANG_RES[itm_type][chr]['name']
            row['Caption'] = LANG_RES[itm_type][chr]['caption']
            for k, v in cfg.items():
                row[k] = v
    save_table(table, 'ITM_Precious', 'sys')

def patch_locations(base, toml):
    for name, section in toml.items():
        file, name = name.split('/')
        table = get_table(name, file)
        for key, val in section.items():
            fmt_val = 0
            if val:
                if isinstance(val, int):
                    fmt_val = val
                else:
                    chr, ty = val.split('/')
                    fmt_val = base['item'][ty][chr]
            col, id = key.split('#')
            row = row_by_id(table, int(id))
            row[col] = fmt_val
        save_table(table, name, file)

def randomize_locations(toml, seed):
    print(f"Randomizing locations based on {f'seed {seed}' if seed else 'default seed'}")
    random.seed(seed)
    values = [v for _, s in toml.items() for _, v in s.items()]
    random.shuffle(values)
    for _, sec in toml.items():
        for k in sec.keys():
            sec[k] = values.pop()
    print('Random locations:')
    print(toml)
    pass

def main():
    parser = argparse.ArgumentParser(
        prog = 'patch_bdat.py'
    )
    parser.add_argument('bdat_json_path')
    parser.add_argument('--no-locations', action='store_const', const=True, help='Do not edit item locations')
    parser.add_argument('--random-locations', metavar='SEED', nargs='?', default='', help='Randomize unlock kit locations')

    args = parser.parse_args()
    global BDAT_PATH
    BDAT_PATH = args.bdat_json_path

    langs = glob.glob('lang_*.toml', root_dir='cfg')
    langs = [l.removeprefix('lang_').removesuffix('.toml') for l in langs]
    with open('cfg/unlocks.toml') as f:
        toml = tomllib.loads(f.read())
    for lang in langs:
        print(f"Patching language {lang}")
        with open(f"cfg/lang_{lang}.toml") as f:
            lang_toml = tomllib.loads(f.read())
        patch_lang(lang_toml, lang)
    patch_items(toml)
    if not args.no_locations:
        if os.path.isfile('cfg/locations.toml'):
            with open('cfg/locations.toml') as f:
                loc_toml = tomllib.loads(f.read())
            if args.random_locations != '':
                # None means the user used --random-locations without a seed
                # while '' means the argument is absent
                randomize_locations(loc_toml, args.random_locations)
            patch_locations(toml, loc_toml)

if __name__ == '__main__':
    main()
