#!/usr/bin/env python3
"""Check compact public TCAP documentation and assigned record values."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    direct = json.loads((ROOT/'docs/engineering/contracts/tcap-2.0.json').read_text())
    direct_doc = (ROOT/'docs/engineering/TCAP-Direct-ABI.md').read_text()
    assert direct['version'] == [2,0] and direct['record_bytes'] == 8
    assert direct['full_path_limit_bytes_by_personality'] == {'ADM3A':1280,'VT52':1280,'ANSI':1792}
    cursor = 0
    for name,offset,size in direct['record_header']:
        assert offset == cursor and size > 0,name
        cursor += size
    assert cursor == 8 and set(direct['operations']) == set(map(str,range(8)))
    assert direct['same_provider_index_required'] and direct['rediscover_after_layout_mutation']
    assert direct['permanent_display_reservation_bytes'] == 0
    assert direct['utility_migrations'] == direct['release_assignment'] == 'deferred'
    for name,mask,strong in [('adm3a',15,2),('vt52',7,0),('ansi',15,2)]:
        text=(ROOT/'src/rsx/compact'/(name+'.mac')).read_text()
        assert "D_DESC: DB 'TC',2,8,24,80,%d,%d"%(mask,strong) in text,name
        assert 'D_TCAP:' in text and 'D_ENTRY:' in text
    assert 'TCAP 2.0' in direct_doc and 'same provider index' in ' '.join(direct_doc.split())
    return {'status':'PASS','scope':'compact public documentation/schema consistency; runtime qualification separate',
            'direct_header_bytes':8,'full_path_limits':direct['full_path_limit_bytes_by_personality']}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
