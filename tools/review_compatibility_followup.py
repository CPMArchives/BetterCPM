#!/usr/bin/env python3
"""Review retained command/provider evidence against the complete predicates."""
import json
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
R=Path(__file__).resolve().parents[1];B=R/'build/compatibility'
p=B/'campaign-manual.json';out=json.loads(p.read_text())
def put(items,result,detail,evidence):
 for item in items.split():out[item]={'result':result,'detail':detail,'evidence':str(evidence.relative_to(R))}
def screen(root,name):return (root/name/'screens.txt').read_text()
a=B/'acquisition-20260907-235356'
assert json.loads((a/'mixed/result.json').read_text())['passed']
assert 'A0>nAmE mIxEd' in screen(a,'mixed') and 'TAIL[ MIXED]' in screen(a,'mixed')
put('0020 0477 0481','P','Raw mixed-case input with backspace edit remained undispatched before host CR; resulting transient identity and uppercase tail verified.',a/'mixed/screens.txt')
assert json.loads((a/'tab/result.json').read_text())['passed']
put('0480','P','Raw TAB did not act as SPACE: NAME<TAB>MIXED did not execute NAME; following CR returned command error.',a/'tab/screens.txt')
c=B/'ccp-20260907-234543';s=screen(c,'identity')
assert 'MARK A0 DU A/00 TAIL[]' in s and 'A0>NAME.COM\n?' in s and 'A0>NAME.TXT\n?' in s
put('0487 0492 0503','P','Bare NAME executed its controlled COM and returned via RET; explicit .COM/.TXT forms were rejected; subsequent VER succeeded.',c/'identity/screens.txt')
s=screen(c,'lookup')
assert all(x in s for x in ['A0>B:\nB0>','MARK B0 DU B/00','B0>ONLYA\n?','MARK A0 DU B/00','B0>A:MISSING\n?','BetterCP/M 0.3'])
put('0475 0485 0486 0489 0493 0495','P','Controlled A/B collision, B-only default search, explicit-A success/failure and following B prompt/BDOS drive query agreed.',c/'lookup/screens.txt')
s=screen(c,'users');assert all(x in s for x in ['MARK B1 DU B/01','MARK B0 DU B/00','MARK B15 DU B/0F','B: PRIVATE  TXT'])
put('0494 0567','P','USER selected distinct executable copies in users 0/1/15; transient Function 32 matched and user-1 directory visibility was isolated.',c/'users/screens.txt')
assert 'B15>USER 16\nB16>' in s
put('0578','F','Stock USER rejects 16; BetterCP/M intentionally accepts 0..31. Preserve the extension and record this baseline divergence for the release profile.',c/'users/screens.txt')
s=screen(c,'exact')
assert 'MARK COLLIDE-DI' in s and 'MARK COLLIDE-DIRX' in s
for name in ['DIR','ERA','TYPE','REN','SAVE','USER']:assert 'MARK COLLIDE-'+name+' DU' not in s
put('0482 0483 0484 0569','P','All six standard exact names took the built-in/CPX branch despite colliding COMs; DI and DIRX executed their distinct COM markers.',c/'exact/screens.txt')
s=screen(c,'missingtools');assert all(x in s for x in ['A0>STAT\n?','A0>SUBMIT TEST\n?','A0>XSUB\n?'])
put('0612','F','STAT device-assignment utility is absent from the supplied system image.',c/'missingtools/screens.txt')
put('0620 0621','F','SUBMIT and XSUB are absent; submitted-command and transient buffered-input scenarios cannot execute in this distribution.',c/'missingtools/screens.txt')
c=B/'ccp-20260907-235509';s=screen(c,'types')
assert all(x in s for x in ['FIRST\nLAST','TYPE EMPTY.TXT','LONGSTART','LONGEND','A       C','CONTROLEND','TYPE MISSING.TXT\n?','BetterCP/M 0.3']) and 'HIDDEN' not in s
put('0577','P','TYPE covered ordinary/empty/multirecord files, TAB/backspace/CR/LF, Ctrl-Z termination and missing-file recovery.',c/'types/screens.txt')
s=screen(c,'directory');assert 'B0>DIR ONE.TXT\nB: ONE' in s and 'O: ONE' not in s
assert 'DIR SYS.TXT\n\nB0>' in s and 'A: BTONE    DAT' in s and 'B: PRIVATE  TXT : NEW      TXT' in s
put('0570','P','Blank, exact, wildcard, SYS-hidden, missing, explicit-drive and alternate-user DIR cases passed after the drive-label repair.',c/'directory/screens.txt')
def files(image):
 raw=extract_raw(image.read_bytes());result={}
 for off in range(0,4096,32):
  e=raw[off:off+32]
  if e[0]>=16:continue
  key=(e[0],bytes(x&127 for x in e[1:12]));content=bytearray();remaining=e[15]*128
  for j in range(16,32,2):
   block=int.from_bytes(e[j:j+2],'little')
   if block and remaining:
    n=min(2048,remaining);content+=raw[block*2048:block*2048+n];remaining-=n
  result.setdefault(key,[]).append(((e[14]&63)*32+(e[12]&31),bytes(content)))
 return {k:b''.join(v for _,v in sorted(parts)) for k,parts in result.items()}
f=files(c/'rename/b.dmk');before=files(c/'b.dmk')
assert (0,b'ONE     TXT') not in f and f[(0,b'NEW     TXT')]==before[(0,b'ONE     TXT')]
assert f[(1,b'NEW     TXT')]==before[(1,b'NEW     TXT')] and f[(0,b'TWO     TXT')]==before[(0,b'TWO     TXT')]
s=screen(c,'rename');assert all(x in s for x in ['FILE EXISTS','NO FILE','REN B:X.TXT=A:BTONE.DAT\n?','BetterCP/M 0.3'])
put('0574','P','REN success, collision, missing source and conflicting drives checked; same target name in user 1 was preserved and did not prevent user-0 rename.',c/'rename/screens.txt')
f=B/'run-20260907-234825/FAULTIO_VER_r/screens.txt';s=f.read_text();assert 'READ CALLER RESUMED' in s and 'WRITE CALLER RESUMED' in s
put('0395 0396 0397 0586 0587','BLOCKED','Prerequisite Bad Sector operator path is absent (0394/0581 fail); no ignore/abort prompt exists at which to conduct this test.',f)
# SAVE is primed after warm reconstruction, immediately before its command.
v=B/'acquisition-20260908-000625/prime';f=files(v/'b.dmk')
assert f[(0,b'MEM     BIN')]==bytes([0xA5])*512
put('0575','P','Controlled provider primed 0100H..02FFH immediately before SAVE 2; saved file contains exactly 512 A5 bytes.',v/'b.dmk')
c=B/'ccp-20260908-000740';f=files(c/'eraseall/b.dmk');before=files(c/'b.dmk')
assert not any(k[0]==0 for k in f) and all(f[k]==data for k,data in before.items() if k[0]==1)
s=screen(c,'eraseall');assert 'ALL (Y/N)? N' in s and 'B: ONE' in s and 'ALL (Y/N)? Y' in s and 'NO FILE' in s
f=files(c/'erase/b.dmk');assert (0,b'ERASE   TMP') not in f and all(f[k]==data for k,data in before.items() if k[0]==1)
put('0572','P','Exact and partial-wildcard erases and all-wildcard N/Y tested; full user-0 erase spans directory records and preserves every user-1 file.',c/'eraseall/screens.txt')
put('0590','P','Full advertised TPA overwritten after adopting private stack; direct warm restart restored CCP/CPXs and a usable system, including a loaded RSX.',B/'final-tpa.log')
assert 'survival passed' in (B/'final-tpa.log').read_text()
put('0391','P','Real emulator write protection produced nonzero BIOS WRITE status; removing protection restored zero and a verified 128-byte transfer.',B/'bios-boundary/457/screens.txt')
put('0600','P','Public BIOS setup/translation/DMA and real scratch-sector transfer/status verified independently of BDOS file services.',B/'bios-boundary/457/screens.txt')
put('0606','P','Direct BIOS TAB remained a raw byte while BDOS console TAB expanded; public logical character interfaces checked separately.',B/'run-20260907-224546/CONSTEST_0077/final.txt')
put('0607','P','Distinct console, reader, punch and list endpoints exercised through the real BDOS with declared public-vector instruments; no physical printer qualification claimed.',B/'run-20260907-233043/MORECHAR/rows.txt')
put('0393 0405','F','Final physical BIOS errors return through the BDOS file-call result path instead of the operator path; successful and disk-full logical cases pass separately.',B/'run-20260907-234825/FAULTIO_VER_r/screens.txt')

v=B/'load-boundary-20260908-002153'
assert 'LOADOK FIT' in (v/'FIT/screens.txt').read_text() if (v/'FIT/screens.txt').exists() else 'LOADOK FIT' in (B/'load-boundary-retest.log').read_text()
assert "OVER\\n?" in (B/'load-boundary-retest.log').read_text()
put('0496 0499','P','Every byte in a 382-record patterned COM checked at runtime; 383-record COM rejected before resident overwrite, followed by usable VER.',B/'load-boundary-retest.log')
s=(B/'loader-results.log').read_text();assert 'Resident USER reparsed' in s and 'provider FF' in s
put('0488 0497 0501 0540','P','Assembled CCP: declared EOF/read-error providers prove preparation only after successful loading and no execution on error/oversize. Resident USER operand reparsed without altering transient FCB/tail area.',B/'loader-results.log')
assert json.loads((B/'readerr-20260908-002033/result.json').read_text())['passed']
put('0390','P','Real BIOS read succeeded with media; documented confirmed eject followed by uncached read returned nonzero.',B/'readerr-20260908-002033/screens.txt')
v=B/'run-20260908-002221'
for n in ('0026','0027','0595'):
 f=next(v.glob('B*'+n+'*/screens.txt'));s=f.read_text();assert 'B0>VER\nBetterCP/M 0.3' in s
put('0504','P','Function 0, entry RET and JP 0000H each returned to B0 and executed VER. RET-versus-WBOOT distinction is separately failed under 0509.',v)
put('0516','P','Separate directory exhaustion and allocation exhaustion fixtures returned distinct Make/sequential/random results; assembled BDOS unit regression checks state preservation too.',B/'final-bdos-unit.log')
v=B/'gaps-20260908-004215';s=(v/'screens.txt').read_text()
assert 'RET INVOKED WBOOT' in s
put('0509','F','Entry RET reaches the public WBOOT gateway (instrumented), although all three mechanisms restore a usable CCP. Stock RET-without-WBOOT distinction is not met.',v/'screens.txt')
assert 'NO SPACE' in s and s.count('BetterCP/M 0.3')>=2
put('0579','P','Token/operand/missing-file/collision/count cases in CCP matrix plus real no-space SAVE all return a usable prompt without executing colliding transients.',v/'screens.txt')
assert all(x['attempts']==1 and x['status']==1 for x in json.loads((v/'retry.json').read_text()))
put('0392','F','Declared recoverable seek failure reached once by assembled DC_READ and DC_WRITE; status 1 returned immediately, without the required retry policy.',v/'retry.json')
put('0471','BLOCKED','Absent-reader EOF is checked; this target has no configured normal reader provider, so the required normal-input half remains unqualified.',R/'src/bios/bios.mac')

v=B/'media-20260908-004746';s=(v/'screens.txt').read_text()
assert 'REPLACEMENT DIRECTORY READ' in s and 'MEDIA CHANGE LEFT DRIVE WRITABLE' in s and 'FIXTURE FAILED' not in s
put('0143','F','Logged removable B had nonzero DPB CKS; swapped healthy media, evicted old directory cache through A, and read replacement directory. Function 29 still reported writable.',v/'screens.txt')
v=B/'gaps-20260908-004815';assert all(x['attempts']==1 and x['status']==1 for x in json.loads((v/'retry.json').read_text()))
put('0392','F','Assembled DC_READ/DC_WRITE each returned status 1 after one seek attempt; declared provider would return success on the second attempt.',v/'retry.json')
p.write_text(json.dumps(out,indent=2)+'\n');print(len(out),'reviewed external verdicts')
