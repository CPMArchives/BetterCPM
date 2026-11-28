"""Altair Tarbell media: 1 KiB blocks, eight-bit allocation entries, no skew."""
from pathlib import Path
from fdf_format import select_fdf

ROOT = Path(__file__).resolve().parents[1]


def geometry():
    f = select_fdf(ROOT/'src/platform/altair/ALTRB77.FDF', 'ALTRB77')
    if (f.spt, f.bsh, f.blm, f.exm, f.dsm, f.drm, f.al0, f.al1,
        f.cks, f.off, f.cylinders, f.sides, f.sector_bytes, f.sector_ids) != (
            26, 3, 7, 0, 223, 63, 192, 0, 16, 8, 77, 1, 128, tuple(range(1,27))):
        raise ValueError('Altair geometry no longer matches the controller/installer contract')
    return f


def image(payload, files):
    f = geometry()
    if len(payload) != 160*128:
        raise ValueError('system payload must have 160 records')
    raw = bytearray(b'\xe5' * f.image_bytes)
    raw[:len(payload)] = payload
    directory = f.reserved_records*128
    entry_index, next_block = 0, 2
    seen = set()
    expanded = []
    for item in files:
        filename, data = item[:2]
        user = item[2] if len(item)>2 else 0
        attrs = item[3] if len(item)>3 else (1 if filename.upper()=='BTRO.DAT' else 0)
        expanded.append((filename,data,user,attrs))
        if filename.upper()=='BTUSR.DAT' and user==0:
            expanded.append((filename,data,1,attrs))
    for filename, data, user, attrs in expanded:
        if not 0 <= user <= 15 or not 0 <= attrs <= 7:
            raise ValueError('invalid user/attributes: '+filename)
        parts = filename.upper().split('.')
        if len(parts) != 2 or not 1 <= len(parts[0]) <= 8 or not 1 <= len(parts[1]) <= 3:
            raise ValueError('invalid 8.3 filename: '+filename)
        key = (user,filename.upper())
        if key in seen:
            raise ValueError('duplicate file: '+filename)
        seen.add(key)
        name = (parts[0].ljust(8)+parts[1].ljust(3)).encode('ascii')
        records = (len(data)+127)//128
        padded = data.ljust(records*128, b'\x1a')
        for extent in range(max(1, (records+127)//128)):
            if entry_index > f.drm:
                raise ValueError('Altair directory full')
            count = min(128, max(0, records-extent*128))
            entry = bytearray(32)
            entry[0] = user
            entry[1:12] = name
            for attribute in range(3):
                if attrs & (1<<attribute):
                    entry[9+attribute] |= 128
            entry[12], entry[14], entry[15] = extent & 31, extent >> 5, count
            for slot in range((count+7)//8):
                if next_block > f.dsm:
                    raise ValueError('Altair filesystem full')
                entry[16+slot] = next_block
                start = directory+next_block*1024
                chunk = padded[extent*16384+slot*1024:extent*16384+(slot+1)*1024]
                raw[start:start+len(chunk)] = chunk
                next_block += 1
            start = directory+entry_index*32
            raw[start:start+32] = entry
            entry_index += 1
    return bytes(raw)


DISKDEFS = '''# Linear host view of 77 tracks x 26 sectors x 128 bytes.
# LibDsk rounds an odd physical track count down; one-record logical
# tracks preserve all byte offsets and the exact 224-block allocation area.
diskdef bettercpm-altair
 seclen 128
 tracks 2002
 sectrk 1
 blocksize 1024
 maxdir 64
 skew 0
 boottrk 208
 os 2.2
end
'''
