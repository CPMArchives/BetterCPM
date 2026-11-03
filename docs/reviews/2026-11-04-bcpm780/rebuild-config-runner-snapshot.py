from pathlib import Path
import sys,json,hashlib
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'licensing-review-20261103/review/tools'))
from build_config import expanded_source,validate_layout
from build_ccp import assemble
receipt=json.loads((p/'bcpm780-binding-review/integration-checkpoint.json').read_text());results={}
for name,info in receipt['platform_artifacts'].items():
 w=p/'bcpm780-normalization-tests/rebuilt'/name;w.mkdir(parents=True,exist_ok=True)
 code=assemble(Path.home()/'bin/z80asm',expanded_source(Path(info['qualified_build_root'])),w/'CONFIG.COM',w/'config.lst',0x100)
 validate_layout(code,(w/'config.lst').read_text());digest=hashlib.sha256(code).hexdigest();assert digest==info['config']['sha256'],(name,digest)
 results[name]={'sha256':digest,'bytes':len(code),'source_commit':receipt['commit'],'layout_check':'PASS'}
(p/'bcpm780-normalization-tests/rebuild-result.json').write_text(json.dumps(results,indent=2));print('PASS both platform CONFIG rebuilds match qualified hashes')
