"""Exercise NOAH's compiled metadata-only help without its overlay."""
from build_noah import help_text, version_text
from test_noah_write import machine

def main():
    m=machine()
    expected=help_text();lines=expected.splitlines()
    assert len(lines)<=23 and all(len(s)<=79 for s in lines)
    assert lines[1:4]==['  - - -',' | Archive Utility',' |']
    assert lines[-2:]==['     /HELP              Display this help.','     /VER               Display utility identification.']
    for tail in ('/HELP','/help /VER BAD','/VER /HELP /BOGUS'):
        text=m.run(tail,{})
        assert expected.strip() in text,text
        assert not m.overlay_events and not m.files
    assert version_text().splitlines()[0]==lines[0]
    assert 'Development' not in m.run('/VER',{})
    print('NOAH compiled help layout, query isolation and screen bounds: PASS')

if __name__=='__main__':main()
