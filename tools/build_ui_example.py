#!/usr/bin/env python3
"""Build the runnable developer example, outside distribution manifests."""
from pathlib import Path
from build_ccp import assemble
from shared_ui import ROOT,UI,input_source,controller_source
from build_shared_ui_fixtures import BUILD


def main():
    library=input_source(standard=True,words=True)+'\n'+controller_source(text=True,choice=True)
    library+='\n'+'\n'.join((UI/n).read_text() for n in ('format.inc','default.inc','choiceerror.inc','screen.inc'))
    source=(ROOT/'src/examples/uiexample.mac').read_text().replace('; @library@',library)
    BUILD.mkdir(parents=True,exist_ok=True);(BUILD/'uiex.mac').write_text(source)
    image=assemble(Path.home()/'bin/z80asm',source,BUILD/'uiex.bin',BUILD/'uiex.lst',0x100)
    (BUILD/'UIEX.COM').write_bytes(image);print('UIEX.COM:',len(image),'bytes')


if __name__=='__main__':main()
