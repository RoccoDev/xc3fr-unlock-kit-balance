import json
import sys
import tomllib
import os
import struct

LANG_RES = {
    'gem': {},
    'art': {},
    'accessory': {},
    'affinity': {}
}
BDAT_PATH = ""

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
    with open(path) as f:
        return json.loads(f.read())

def save_table(table, name, file, lang=None):
    assert BDAT_PATH
    path = f"{BDAT_PATH}/{lang}/game/{file}/{name}.json" if lang else f"{BDAT_PATH}/{file}/{name}.json"
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
    return next(row for row in rows if row['$id'] == id)

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
    table = get_table('ITM_Precious', 'sys')

    for itm_type, chrs in items.items():
        for chr, id in chrs.items():
            row = row_by_id(table, id)
            row['Name'] = LANG_RES[itm_type][chr]['name']
            row['Caption'] = LANG_RES[itm_type][chr]['caption']
            row['IconPop'] = 1
    
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

def main():
    langs = ['gb']
    with open('cfg/unlocks.toml') as f:
        toml = tomllib.loads(f.read())
    for lang in langs:
        with open(f"cfg/lang_{lang}.toml") as f:
            lang_toml = tomllib.loads(f.read())
        patch_lang(lang_toml, lang)
    patch_items(toml)
    if os.path.isfile('cfg/locations.toml'):
        with open('cfg/locations.toml') as f:
            loc_toml = tomllib.loads(f.read())
        patch_locations(toml, loc_toml)

if __name__ == '__main__':
    if len(sys.argv) < 2 or not sys.argv[1]:
        print('Usage: python patch_bdat.py /path/to/bdat')
        print('NOTE: Modified BDATs will be overwritten.')
    else:
        BDAT_PATH = sys.argv[1]
        main()