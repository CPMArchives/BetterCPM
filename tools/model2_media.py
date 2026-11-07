"""Physical BCM2SS system media; offset 0 is the first byte of the real FM surface."""
from pathlib import Path
from fdf_format import select_fdf

SOURCE = Path(__file__).resolve().parents[1] / 'src/platform/trs80m2/BCM2SS.FDF'
DIAG = b'DIAG\xc3\x04\x10'
HEADER = b'IMD 1.18: 01/01/2000 00:00:00\r\nBetterCP/M BCM2SS\r\n\x1a'


def geometry():
    f = select_fdf(SOURCE, 'BCM2SS')
    if (f.cylinders, f.sides, f.boot_encoding, f.boot_psectors, f.boot_secsize,
            f.physical_sectors, f.sector_bytes, f.off, f.dsm, f.drm) != (
            77, 1, 'FM', 26, 128, 16, 512, 4, 291, 127):
        raise ValueError('BCM2SS no longer matches the ROM and BIOS transfer contract')
    if (f.flags, f.sector_ids, f.boot_sector_ids, f.spt, f.bsh, f.blm, f.exm,
            f.al0, f.al1, f.cks) != (128, tuple(range(1,17)), tuple(range(1,27)),
                                    64,4,15,0,192,0,32):
        raise ValueError("disk binding differs from BCM2SS")
    return f


def image(payload, files, bootable=True):
    """Use the maintained 2 KiB/16-bit filesystem installer on actual data bytes."""
    from build_trs80_boot import install_files
    f = geometry()
    if len(payload) != 160*128:
        raise ValueError('system package must be exactly 160 records')
    if bootable and payload[512:516] != b'BOOT':
        raise ValueError('missing Model II ROM entry at package record 4')
    boot = bytearray(b'\xe5' * (f.boot_psectors*f.boot_secsize))
    boot[:384] = payload[:384]
    boot[512:1024] = payload[512:1024]
    boot[1536:1664] = payload[384:512]
    if bootable and not boot[1536:1664].startswith(DIAG):
        raise ValueError("missing ROM diagnostic vector in package record 3")
    tail = bytearray(b'\xe5' * ((f.cylinders-1)*f.raw_track_bytes))
    tail[:len(payload)-1024] = payload[1024:]
    directory = (f.off-1)*f.raw_track_bytes
    if len(tail)-directory != (f.dsm+1)*f.block_bytes:
        raise ValueError('filesystem capacity does not end on final physical sector')
    install_files(tail, files, directory=directory, block_count=f.dsm+1)
    output = bytearray(HEADER)
    for cyl in range(f.cylinders):
        if cyl:
            size, code, mode = 512, 2, 3
            data = tail[(cyl-1)*8192:cyl*8192]
            ids = tuple((i*11) % 16 + 1 for i in range(16))  # 3 slots from ID n to n+1
        else:
            size, code, mode = 128, 0, 0
            data = boot
            ids = f.boot_sector_ids
        output.extend((mode, cyl, 0, len(ids), code, *ids))
        for ident in ids:
            sector = data[(ident-1)*size:ident*size]
            if sector == sector[:1]*size:
                output.extend((2,sector[0]))
            else:
                output.append(1)
                output.extend(sector)
    return bytes(output)
