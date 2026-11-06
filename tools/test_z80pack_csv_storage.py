"""Execute BDOS checksums against the actual RAM build's four protected CSVs."""
from pathlib import Path
import argparse,json
from test_bios import Z80
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,default=ROOT/'build/z80pack');a=p.parse_args()
    layout=json.loads((a.build/'checksum-layout.json').read_text());addresses=layout['csv_addresses']
    assert layout['cks_limit']==48 and layout['boot_surface_capability']
    assert (layout['tpa'],layout['history'])==(L['TPA'],L['HISTORY'])
    resident=(a.build/'resident.bin').read_bytes();bios=(a.build/'bios.bin').read_bytes()
    tables=(a.build/'tables.bin').read_bytes();state=symbols(ROOT/'build/bdos/bdos.lst')
    assert all(int.from_bytes(tables[i*80+12:i*80+14],'little')==addresses[i] for i in range(4))
    intervals=[set(range(x,x+48)) for x in addresses]
    assert all(not intervals[i]&intervals[j] for i in range(4) for j in range(i))
    assert layout['extra_mutable_region']==[L['FILE']-96,L['FILE']]
    assert L['BIOS']+len(bios)<=L['FILE']-96
    cpu=Z80(b'');cpu.sp=0x7800;cpu.mem[L['SYSTEM']:L['SYSTEM']+len(resident)]=resident
    assert bytes(cpu.mem[L['FILE']-96:L['FILE']])==bytes(96),'cold carrier does not initialize extra CSVs'
    for x in addresses:cpu.mem[x:x+48]=bytes([165])*48
    expected={x:bytearray([165]*48) for x in addresses}
    table_before=bytes(cpu.mem[L['TABLES']:L['TABLES']+576])
    cpu.setword(state['UB_DIRBUF'],0x7000)
    cpu.mem[state['UBS_LOGIN']]=0
    for drive,cks in enumerate((32,48,48,48)):
        cpu.setword(state['UB_DPH'],L['TABLES']+drive*80)
        cpu.mem[state['UB_DPBC']+11]=cks
        cpu.mem[state['UB_CTXDRV']]=drive
        for record in range(49):
            cpu.mem[0x7000:0x7080]=bytes([record+1])+bytes(127)
            cpu.mem[state['UBS_CREC']]=record;cpu.a=0
            cpu.run(state['UB_CSUM'])
            if record<cks:expected[addresses[drive]][record]=record+1
            for x in addresses:assert bytes(cpu.mem[x:x+48])==expected[x],(drive,record,x)
            assert bytes(cpu.mem[L['BIOS']:L['BIOS']+len(bios)])==bios
        # A changed last checked directory record must protect a logged drive,
        # retaining its previous checksum until the drive is reset/relogged.
        cpu.mem[state['UBS_LOGIN']]=1<<drive;cpu.mem[state['UB_RDONLY']]=0
        cpu.mem[state['UBS_CREC']]=cks-1;cpu.mem[0x7000]=177;cpu.a=0
        cpu.run(state['UB_CSUM'])
        assert cpu.mem[state['UB_RDONLY']] & (1<<drive)
        assert bytes(cpu.mem[addresses[drive]:addresses[drive]+48])==expected[addresses[drive]]
        cpu.mem[state['UBS_LOGIN']]=0;cpu.a=0;cpu.run(state['UB_CSUM'])
        expected[addresses[drive]][cks-1]=177
    want=bytearray(table_before)
    for x,values in expected.items():
        if L['TABLES']<=x<L['TABLES']+576:want[x-L['TABLES']:x-L['TABLES']+48]=values
    assert bytes(cpu.mem[L['TABLES']:L['TABLES']+576])==want,'CSV touched binding, ALV, or unused tail'
    print('PASS four CSV regions: cold zeros, independent 32/48-byte checksums, full final-record media-change detection, bounds; BIOS/ALV/TPA/history preserved')
if __name__=='__main__':main()
