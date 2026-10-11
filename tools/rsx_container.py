"""Ordered internal helper slots; names remain diagnostic build artifacts."""
NAMES = ('R3PLAN','R3SLOTS','R3SNAP','R3CARR','R3META','R3COORD',
         'R3PROF','R3KCTX','R3KEEP','R3KPRE','R3FINAL','R3DROP',
         'R3MOVE','R3COMIT','R3RESOL')
PACK_NAME = 'R3PACK.RSX'
SLOT_BYTES = 1024
PACK_BYTES = len(NAMES) * SLOT_BYTES

def constants():
    return '\n'.join(f'{name}_RECORD EQU {i*8}' for i,name in enumerate(NAMES))

def pack(images):
    result = b''.join(images[name+'.RSX'] for name in NAMES)
    if any(len(images[name+'.RSX']) != SLOT_BYTES for name in NAMES):
        raise ValueError('RSX container slot is not exactly 1024 bytes')
    assert len(result) == PACK_BYTES < 16384
    return result
