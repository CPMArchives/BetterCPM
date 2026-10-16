#!/usr/bin/env python3
"""Exercise actual BDOS 178 through portable personalities and both backends."""
from pathlib import Path
from system_layout import LAYOUT
from test_screen_backends import ROOT, fixture, load
from test_vt52_foundation import symbols


def main():
    bdos=symbols(ROOT/'build/bdos/bdos.lst')
    for name in ('M4SCRN','ANSISCRN'):
        table=symbols(ROOT/'build/screen-backends'/(name+'.lst'))
        # Force the callback dispatch's E scratch value to zero. Without
        # preserving original DE, BF_CURSOR then mistakes a draw for a query.
        target=table['S_PUT' if name=='M4SCRN' else 'B_PUT']
        backbase=0x6000+((-target)&255)
        for stem,directory,prefix in [('adm3a','monitor-development','AM'),('vt52','vt52-development','VT')]:
            cpu,_,cells,_=fixture(name,backbase,cpmsim_bios=ROOT/'build/audit/release-090-z80pack')
            base=0x7000;syms=load(cpu,ROOT/'build'/directory,stem,base)
            entry=syms[prefix+'_ENTRY']+base-0x8000
            cpu.setword(base+12,cpu.backend_entry)
            image=(ROOT/'build/bdos/bdos.bin').read_bytes()
            cpu.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+len(image)]=image
            biosdir=ROOT/('build/bios' if name=='M4SCRN' else 'build/audit/release-090-z80pack')
            bios=symbols(biosdir/'bios.lst');cpu.setword(bios['MP_MON'],entry)
            cpu.a=4;cpu.run(entry,limit=200000)
            ext=(ROOT/'build/system/extensions.bin').read_bytes()
            cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(ext)]=ext
            column=bdos['UB_COLUMN'];cpu.mem[column]=0
            def invoke(char):
                sp=cpu.sp;cpu.c,cpu.e=178,char
                cpu.run(LAYOUT['EXTENSIONS'],limit=200000)
                assert cpu.sp==sp
                return cpu.a
            assert invoke(0)==1 and cpu.mem[column]==0
            assert invoke(ord('X'))==1 and cpu.mem[column]==1
            assert cells()[0]==ord('X')|128
            assert invoke(0)==1 and cpu.mem[column]==1
            cpu.a,cpu.c=0,ord('N');cpu.run(entry,limit=200000)
            assert cells()[1]==ord('N')
            if name=='M4SCRN':
                class Keyboard(bytearray):
                    scans=0
                    def __getitem__(self,key):
                        if key==0xF404:
                            self.scans+=1
                            return 4 if self.scans<=3 else 0  # R held, then released
                        return super().__getitem__(key)
                cpu.mem=Keyboard(cpu.mem)
                cpu.mem[3]=0x95
                cpu.c,cpu.e=6,255
                cpu.run(LAYOUT['BDOS'],limit=200000)
                assert cpu.a==ord('R'),(stem,'polled input',cpu.a,cpu.mem.scans)
            print(f'PASS {stem}/{name}: actual BDOS 178 query, reverse draw/advance and relocation-sensitive E preservation')


if __name__=='__main__':main()
