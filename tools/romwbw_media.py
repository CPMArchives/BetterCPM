"""Fixed hd512 filesystem and RomWBW disk boot metadata for initial bring-up.

1040 tracks of 64 CP/M records; 16 reserved tracks; 4 KiB allocation blocks.
The raw image is 8 MiB data plus 128 KiB system area. No MBR or slice offset.
"""
import struct

SIZE = 1040 * 64 * 128
DIRECTORY = 16 * 64 * 128

def tables(layout):
    dpb = struct.pack('<HBBBHHBBHH',64,5,31,1,2047,511,0xF0,0,0,16)
    mapping=b'HB'+bytes((1,0))+struct.pack('<HII',512,0,16640)+bytes(34)
    data=bytearray()
    for drive in range(2):
        data+=struct.pack('<8H',0,0,0,0,layout['DIRBUF'],layout['TABLES']+80*drive+17,
                          0,layout['TABLES']+160+256*drive)
        data+=bytes((0 if drive==0 else 255,))+dpb+mapping
    return bytes(data)+bytes(512)

def configuration(unit=255):
    record=bytearray(512);record[:8]=b'BWCF'+bytes((1,2,unit,0))
    checksum=-sum(struct.unpack('<256H',record))&65535
    struct.pack_into('<H',record,8,checksum)
    return bytes(record)

def image(payload, boot, files):
    if len(payload)!=20480 or not 0 < len(boot)<=512:
        raise ValueError('boot/package size')
    raw=bytearray(b'\xe5'*SIZE)
    raw[32768:32768+len(payload)]=payload
    # The shared PDS/startup reader uses BIOS records 1 and 2.
    raw[128:384]=payload[128:384]
    raw[1536:2048]=boot.ljust(512,b'\0')
    info=bytearray(512)
    struct.pack_into('<H',info,384,0xA55A)
    info[487:503]=b'BETTERCPM HBIOS'.ljust(16,b' ')
    info[503]=ord('$')
    struct.pack_into('<4H',info,504,0,0x1000,0x1200,0x1000)
    raw[1024:1536]=info
    raw[2048:2560]=configuration()
    entry_index,block=0,4
    for filename,data in files:
        stem,extension=filename.upper().split('.')
        if not (1<=len(stem)<=8 and 1<=len(extension)<=3):raise ValueError(filename)
        records=(len(data)+127)//128
        data=data.ljust(records*128,b'\x1a')
        for extent in range(max(1,(records+255)//256)):
            count=min(256,records-extent*256)
            entry=bytearray(32);entry[1:12]=(stem.ljust(8)+extension.ljust(3)).encode('ascii')
            logical=extent*2+(1 if count>128 else 0)
            entry[12],entry[14],entry[15]=logical&31,logical>>5,(count-1)%128+1 if count else 0
            for slot in range((count+31)//32):
                if block>2047:raise ValueError('disk full')
                struct.pack_into('<H',entry,16+2*slot,block)
                chunk=data[extent*32768+slot*4096:extent*32768+(slot+1)*4096]
                start=DIRECTORY+block*4096;raw[start:start+len(chunk)]=chunk;block+=1
            if entry_index>=512:raise ValueError('directory full')
            start=DIRECTORY+entry_index*32;raw[start:start+32]=entry;entry_index+=1
    assert len(raw)==SIZE
    return bytes(raw)

DISKDEFS = """diskdef bettercpm-romwbw
 seclen 128
 tracks 1040
 sectrk 64
 blocksize 4096
 maxdir 512
 skew 0
 boottrk 16
 os 2.2
end
"""
