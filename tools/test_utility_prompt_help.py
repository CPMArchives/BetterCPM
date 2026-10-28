#!/usr/bin/env python3
"""Inline help must repeat the current item without changing its operation."""
from test_crc import execute,name83,records
from test_noah_write import machine
from test_usq_com import diskkey
from test_lbr import archive,entry,with_crcs


def checksum_tests():
    cases=0
    data=records(b'123456789');old=records(b'old list')
    for program in ('CRCKSUM','MD5SUM'):
        files={(2,7,'FIX.DAT'):data,(2,7,'CHECK.LST'):old}
        prompt='C7:CHECK.LST exists.\r\nOverwrite? (Y/n/a/?) '
        for answer in (b'N',b'Y',b'\r',b'A',b'\x03'):
            baseline=execute(files,'FIX.DAT /FILE=CHECK.LST',keys=answer,program=program)
            helped=execute(files,'FIX.DAT /FILE=CHECK.LST',keys=b'??'+answer,program=program)
            assert helped['files']==baseline['files'] and helped['writes']==baseline['writes'],(program,answer,helped['text'])
            assert helped['text'].count(prompt)==3,helped['text']
            assert helped['text'].count('Y Yes, N No, A All, ? Help')==2,helped['text']
            cases+=1
        many={(1,1,'A.DAT'):data,(1,2,'B.DAT'):data,(1,1,'CHECK.LST'):old,(1,2,'CHECK.LST'):old}
        for keys in (b'A',b'??A'):
            result=execute(many,'B[1-2]:*.DAT /LOCAL=CHECK.LST',keys=keys,program=program)
            assert '2 files calculated; 2 lists written.' in result['text'],result['text']
            assert result['text'].count('Overwrite?')==(1 if keys==b'A' else 3),result['text']
            assert result['files'][1,1,name83('CHECK.LST')]!=old and result['files'][1,2,name83('CHECK.LST')]!=old
            cases+=1
        result=execute(files,'FIX.DAT /FILE=CHECK.LST /40',keys=b'?N',program=program)
        assert all(len(line)<=40 for line in result['text'].splitlines()),result['text']
        assert result['files'][2,7,name83('CHECK.LST')]==old
        cases+=1
    return cases


def outcome(m):
    return (dict(m.files),dict(m.attrs),list(m.created),list(m.renamed),list(m.deleted))


def noah_tests():
    m=machine();m.instruction_budget=150000000;cases=0
    lib=diskkey(2,'TEXTS.LBR',7);target=diskkey(3,'README.TXT',3)
    raw=with_crcs(archive([entry(b'README  TXT')],b'R'*128))
    files={lib:raw,target:b'OLD'}
    helptext='Y Yes, N No, A All, C Cancel, ? Help'
    for answer in ('Y','N','\r','A','C','\x1b','\x03'):
        m.run('/X B7:TEXTS.LBR C3:',files,keys=answer);expected=outcome(m)
        text=m.run('/X B7:TEXTS.LBR C3:',files,keys='??'+answer)
        assert outcome(m)==expected and text.count(helptext)==2,text
        assert text.count('C3:README.TXT exists. Replace? Y/N/A/C/? [N]:')==3,text
        assert m.answers==[63,63,ord(answer)] and not m.opened,text
        cases+=1
    # /Q keeps authorization/help; /Y remains unattended and never consumes keys.
    text=m.run('/X /Q B7:TEXTS.LBR C3:',files,keys='?N')
    assert helptext in text and m.files[target]==b'OLD',text
    text=m.run('/X /Y B7:TEXTS.LBR C3:',files,keys='?')
    assert not m.answers and helptext not in text and m.files[target]==b'R'*128,text
    cases+=2
    # Protection confirmations are still simple Y/N; ? is not advertised.
    text=m.run('/X /R B7:TEXTS.LBR C3:',files,keys='?N',attributes={target:1})
    assert helptext not in text and 'protected [RO]. Replace? Y/N [N]:' in text and m.files[target]==b'OLD',text
    cases+=1
    # Source/member replacement inside ADD retains member context after help.
    arc=diskkey(1,'NEW.LBR');source=diskkey(2,'README.TXT',7)
    text=m.run('/ADD NEW.LBR B7:README.TXT',{arc:raw,source:b'S'*128},keys='??N')
    assert text.count(helptext)==2 and text.count('README')>=3 and m.files[arc]==raw,text
    cases+=1
    # Safe recovery decisions retain their state for Retry, Skip/default and Abort.
    for command,inputs in (('/ADD NEW.LBR B7:README.TXT',{source:b'S'*128}),
                            ('/SQ B7:README.TXT C3:',{source:b'S'*128})):
        for answer in ('R','S','\r','A','\x1b','\x03'):
            m.run(command,inputs,failures={'read':1},keys=answer);expected=outcome(m)
            text=m.run(command,inputs,failures={'read':1},keys='??'+answer)
            assert outcome(m)==expected and text.count('R Retry, S Skip, A Abort all, ? Help')==2,text
            assert text.count('B7:README')>=3 and not m.opened,text
            cases+=1
    # Failed extraction and whole-archive replay keep destination/archive context.
    for command,inputs,identity in (
        ('/X B7:TEXTS.LBR C3:',{lib:raw},'C3:README.TXT'),
        ('/ADD NEW.LBR B7:README.TXT',{source:b'S'*128},'NEW.LBR')):
        for answer in ('R','S','A'):
            m.run(command,inputs,failures={'write':1},keys=answer);expected=outcome(m)
            text=m.run(command,inputs,failures={'write':1},keys='??'+answer)
            assert outcome(m)==expected and text.count('R Retry, S Skip, A Abort all, ? Help')==2,text
            assert text.count(identity)>=3 and not m.opened,text
            cases+=1
    return cases


if __name__=='__main__':
    checks=checksum_tests()
    print(f'CRCKSUM/MD5SUM: {checks} focused prompt-help cases pass',flush=True)
    checks=noah_tests()
    print(f'NOAH: {checks} focused prompt-help cases pass',flush=True)
