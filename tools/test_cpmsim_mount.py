#!/usr/bin/env python3
"""Compile the actual MOUNT host service with a guest-memory adapter.
Exercise real files, hard links and symlinks; no user media is changed.
"""
import argparse, subprocess, tempfile
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
a=p.parse_args()
service=(a.source/'cpmsim/srcsim/mount.inc').resolve()
with tempfile.TemporaryDirectory() as tmp:
    w=Path(tmp)
    harness=r'''
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <assert.h>
#include <stdint.h>
typedef unsigned char BYTE;
static BYTE memory[65536];
static BYTE dma_read(unsigned a) { return memory[a]; }
static void dma_write(unsigned a, BYTE b) { memory[a]=b; }
static char *diskdir=".";
static char diskd[]="disks";
#define DISKSDIR "disks"
static int descriptors[16];
static struct {char *fn; int *fd; unsigned tracks,sectors,sector_size;} disks[16];
#include "SERVICE"
static int request(const char *s,int confirm) {
    assert(strlen(s)<128);memory[0x80]=strlen(s);
    memcpy(memory+0x81,s,strlen(s));mount_command(confirm);
    return memory[0x1fff];
}
int main(void) {
    int d,fd; char name[32];
    mkdir("disks",0700);
    for(d=0;d<4;d++) {
        snprintf(name,sizeof name,"drive%c.dsk",'a'+d);
        disks[d].fn=strdup(name);disks[d].fd=&descriptors[d];
        disks[d].tracks=77;disks[d].sectors=26;disks[d].sector_size=128;
    }
    fd=open("Original.dsk",O_CREAT|O_WRONLY,0600);write(fd,"A",1);close(fd);
    fd=open("New Image.dsk",O_CREAT|O_WRONLY,0600);write(fd,"B",1);close(fd);
    symlink("../Original.dsk","disks/driveb.dsk");
    assert(request("",0)==0 && strstr(mount_output,"Original.dsk"));
    assert(request("/U",0)==1 && !mount_override[1]);
    assert(request("/U [B,Z]:",0)==1 && !mount_override[1]);
    assert(request("/U /L B:",0)==1 && !mount_override[1]);
    assert(request("B: missing.dsk",0)==1 && !mount_override[1]);
    assert(request("C: Original.dsk",0)==1 && !mount_override[2]);
    link("Original.dsk","Hard.dsk"); symlink("Original.dsk","Link.dsk");
    assert(request("C: Hard.dsk",0)==1);assert(request("C: Link.dsk",0)==1);
    assert(request("B: \"New Image.dsk\"",0)==0 && memory[0x1ffd]==2);
    assert(strstr(mount_path[1],"New Image.dsk"));
    assert(request("/LIST [B,C]:",0)==0 && strstr(mount_output,"New Image.dsk"));
    assert(request("/U [A,B,C]:",0)==2 && !mount_override[0] && *mount_path[1]);
    assert(request("/U [A,B,C]:",1)==0 && memory[0x1ffd]==7 && !*mount_path[1]);
    assert(request("A: Original.dsk",0)==2 && !*mount_path[0]);
    assert(request("A: Original.dsk",1)==0 && *mount_path[0]);
    assert(request("/U [B,B]:",0)==1);
    assert(request("[B,C]: Original.dsk",0)==1);
    assert(request("B: /UNMOUNT",0)==0);
    assert(request("/VER",0)==0 && strstr(mount_output,"001-dev"));
    assert(request("/HELP",0)==0 && strstr(mount_output,"working directory"));
    assert(request("B: \"unterminated",0)==1);
    fd=open("Huge.dsk",O_CREAT|O_WRONLY,0600);ftruncate(fd,999999);close(fd);
    assert(request("B: Huge.dsk",0)==1 && !*mount_path[1]);
    assert(request("B: .",0)==1);
    assert(request("/L",0)==0 && !memory[0x1ffd]);
    return 0;
}
'''.replace('SERVICE',str(service))
    (w/'test.c').write_text(harness)
    subprocess.run(['cc','-std=c99','-D_DEFAULT_SOURCE','-Wall','-Wextra','-Werror',str(w/'test.c'),'-o',str(w/'test')],check=True)
    subprocess.run([str(w/'test')],cwd=w,check=True)
print('PASS: MOUNT syntax, atomic validation, image identity, replacement, A: confirmation, reset masks and listing')
