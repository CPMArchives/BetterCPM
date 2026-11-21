"""PDS ABI 2 metadata and exact cold-layout arithmetic for host tooling."""
import struct

HISTORY = (0, 128, 192, 384)
MCL = (0, 128)
VARIABLES = (0, 128, 256, 512)
HEADER_BYTES = 12


def header(history=2, mcl=0, variables=0):
    try:
        if min(history, mcl, variables) < 0:
            raise IndexError
        lengths = HISTORY[history], MCL[mcl], VARIABLES[variables]
    except (IndexError, TypeError):
        raise ValueError('invalid PDS capacity choice') from None
    data = bytearray(struct.pack('<2sBB4H', b'PD', 2, 12, *lengths, 0))
    struct.pack_into('<H', data, 10, -sum(struct.unpack('<6H', data)) & 65535)
    return bytes(data)


def layout(data, system_base):
    if len(data) != 12 or data[:4] != b'PD\x02\x0c':
        raise ValueError('invalid PDS header')
    words = struct.unpack('<6H', data)
    lengths = words[2:5]
    if sum(words) & 65535 or any(n not in choices for n, choices in
            zip(lengths, (HISTORY, MCL, VARIABLES))):
        raise ValueError('invalid PDS lengths or checksum')
    low = system_base-12-sum(lengths)
    if low < 0x100 or system_base > 65535:
        raise ValueError('PDS outside protected address space')
    owners = {}
    cursor = low
    for name, size in zip(('HISTORY', 'MCL', 'VAR'), lengths):
        owners[name] = (cursor, size)
        cursor += size
    return dict(low=low, total=12+sum(lengths), metadata=12, owners=owners,
                unloaded_com=(low-3-256)//128*128)
