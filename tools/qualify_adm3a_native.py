#!/usr/bin/env python3
"""Capture ADM-3A visual pages and an original MM CONFIG menu on private media."""
import argparse
import subprocess
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file, build
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, DIRECTORY_ENTRIES
from run_trs80_command import key_args, DEFAULT_EMULATOR
from trs80gp_launch import run as launch

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=ROOT/'build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk')
    parser.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    parser.add_argument('--application',action='store_true',help='capture original MM CONFIG startup instead of ADMTST pages')
    parser.add_argument('--bell',action='store_true',help='record the provider bell with emulator sound effects muted')
    parser.add_argument('--editing-trace',action='store_true',help='capture immediately after typed editing input, without claiming qualification')
    parser.add_argument('--editing',action='store_true',help='check command-line Backspace with the loaded monitor')
    parser.add_argument('--manual-load',action='store_true',help='legacy option; the private startup script now always loads the pair')
    args=parser.parse_args()
    if args.editing_trace:args.editing=True
    if sum([args.bell,args.application,args.editing])>1:parser.error('choose one campaign')
    parent=ROOT/'build/monitor-development/native-campaign'
    parent.mkdir(parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='bell-' if args.bell else ('application-' if args.application else ('editing-' if args.editing else 'pages-')),dir=parent))
    raw=extract_raw(args.image.read_bytes())
    for index in range(DIRECTORY_ENTRIES):
        offset=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+index*32
        if raw[offset+1:offset+9] in [b'R3PACK  ',b'ADM3A   ',b'ADMTST  ',b'M4SCRN  ',b'STARTUP ']:raw[offset]=229
    files=[('R3PACK.RSX',ROOT/'build/system/R3PACK.RSX'),
           ('M4SCRN.RSX',ROOT/'build/screen-backends/M4SCRN.RSX'),
           ('ADM3A.RSX',ROOT/'build/monitor-development/ADM3A.RSX'),
           ('ADMTST.COM',ROOT/'build/monitor-development/ADMTST.COM')]
    if args.application:
        files += [('MMCONF.COM',ROOT/'third_party/montezuma/CONFIG-3.10.COM'),
                  ('DISK.FDF',ROOT/'third_party/montezuma/DISK.FDF')]
    for name,path in files:add_file(raw,name,path.read_bytes())
    if args.bell:
        # Standard CP/M raw console output BEL, followed by warm return.
        add_file(raw,'BELLTST.COM',bytes.fromhex('0e061e07cd0500c30000'))
    if args.editing:
        add_file(raw,'READY.COM',bytes.fromhex('110b010e09cd0500c30000')+b'\x1aMONITOR EDIT READY\r\n$')
        add_file(raw,'ENDCHK.SUB',b'RSX UNLOAD ADM3A\r\nRSX UNLOAD M4SCRN\r\nRSX LIST\r\n\x1a')
    program='READY' if args.editing else ('BELLTST' if args.bell else ('MMCONF' if args.application else 'ADMTST'))
    startup=(':VER /BANNER\r\nRSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n'+program+'\r\n')
    if not args.application and not args.editing:
        startup+='RSX UNLOAD ADM3A\r\nRSX UNLOAD M4SCRN\r\nRSX LIST\r\n'
    add_file(raw,'STARTUP.SUB',startup.encode('ascii')+b'\x1a')
    image=out/'private-system.dmk'
    image.write_bytes(build(bytes(raw)))
    command=[str(args.emulator),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000']
    if args.bell:
        command+=['-sfmute','-ir','audio','-iw','No RSXs loaded','-iw','TPA available: 53K',
                  '-id','120','-ir','audio','-it','-ics','-ix']
    elif args.editing:
        command+=['-iw','MONITOR EDIT READY','-id','6000']
        if args.editing_trace:command+=['-it','-ics']
        command+=key_args('RSX LISX\x08T\r',delay=60)
        if args.editing_trace:
            command+=['-id','1500','-it','-ics','-ix']
        else:
            command+=['-iw','TPA available:','-id','6000','-it','-ics']
        if not args.editing_trace:command+=key_args('SUBMIT ENDCHK\r',delay=60)+['-iw','No RSXs loaded','-iw','TPA available: 53K','-id','120','-it','-ics','-ix']
    elif args.application:
        command+=['-iw','Your choice:','-id','120','-it','-ics','-ix']
    else:
        for index,marker in enumerate(['Marker: row 5','Parser reset:','TAB should put','Cursor OFF/ON query passed.']):
            if index:command+=key_args(' ',delay=60)
            command+=['-iw',marker,'-iw','Press a key to continue.','-id','120','-it','-ics']
        command+=key_args(' ',delay=60)+['-iw','No ENTER is required.']
        command+=key_args('A:[]',delay=60)+['-iw','ADMTST keyboard checks passed.','-id','120','-it','-ics']
        command+=['-iw','No RSXs loaded','-iw','TPA available: 53K','-id','120','-it','-ics','-ix']
    launch(command,cwd=out,check=True,timeout=240)
    captures=sorted(out.glob('trs80-text-*.bin'))
    assert captures,'no emulator captures'
    for path in captures:
        print(path)
        data=path.read_bytes()[:1920]
        for row in range(24):
            line=bytes(c&127 for c in data[80*row:80*(row+1)]).decode('ascii').rstrip()
            if line:print(line)
    if args.editing_trace:
        print('Diagnostic editing capture only; no qualification claimed')
        return
    if args.editing:
        assert len(captures)==2
        first=bytes(c&127 for c in captures[0].read_bytes()[:1920])
        final=bytes(c&127 for c in captures[1].read_bytes()[:1920])
        assert b'A0>RSX LIST' in first and b'ADM3A' in first and b'M4SCRN' in first
        assert b'No RSXs loaded' in final and b'TPA available: 53K' in final
        print('PASS: real Model 4 command-line Backspace/redisplay with portable ADM3A and unload/53K')
    if args.application:
        screen=bytes(c&127 for c in captures[0].read_bytes()[:1920])
        for marker in [b'CONFIG version 3.10',b'Configuration options:',
                       b'Video Display definitions',b'Your choice:']:
            assert marker in screen,marker
        print('PASS: original MM CONFIG opening screen; configuration operations not exercised')
    if args.bell:
        import wave
        recordings=list(out.glob('*.wav'))
        assert len(recordings)==1,recordings
        with wave.open(str(recordings[0]),'rb') as wav:
            width=wav.getsampwidth()
            channels=wav.getnchannels()
            samples=wav.readframes(wav.getnframes())
        silence=bytes([128])*len(samples) if width==1 else bytes(len(samples))
        assert samples and samples!=silence,'bell recording is silent'
        values=[int.from_bytes(samples[i:i+width],'little',signed=width!=1)
                for i in range(0,len(samples),width*channels)]
        center=128 if width==1 else 0
        crossings=sum((a>center)!=(b>center) for a,b in zip(values,values[1:]))
        assert crossings==512,('unexpected bell waveform',crossings)
        print(f'PASS: native bell recording with 512 transitions, effects muted: {recordings[0]}')
    elif not args.application and not args.editing:
        assert len(captures)==6
        movement=captures[2].read_bytes()
        assert movement[160:164]==b'LEFT'
        assert movement[248:250]==b'AB'
        assert movement[320:325]==b'RIGHT'
        video=captures[3].read_bytes()
        assert video[87:89]==bytes([ord('O')|128,ord('N')|128])
        assert video[90:93]==b'OFF'
        assert video[800:806]==b'LINE A'
        assert video[880:960]==b' '*80
        assert video[960:966]==b'LINE C' and video[1040:1046]==b'LINE D'
        assert any(b'ADMTST keyboard checks passed.' in p.read_bytes() for p in captures)
        assert any(b'TPA available: 53K' in p.read_bytes() for p in captures)
        print('PASS: actual ADMTST completion and 53K TPA restored after unload; inspect visual captures separately')


if __name__=='__main__':main()
