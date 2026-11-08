"""Add audited blank work media to qualified 1.1 System build outputs.

Copies immutable build outputs into a new packaging directory; never rebuilds
or substitutes a System image. Guest qualification remains bound to its hash.
"""
import argparse
import json
from pathlib import Path
import shutil
from package_release_candidates import read_report, sha, ROOT
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from convert_fdf_image import raw_to_dmk
from test_utilities_inventory import inspect


def prepare(sources,output,commit):
    output.mkdir(parents=True,exist_ok=False)
    for target,source in sources.items():
        report,data=read_report(source,commit)
        if report['target']!=target:raise ValueError('wrong target: '+target)
        dest=output/target;shutil.copytree(source,dest)
        if target!='trs80m2':
            native=target=='trs80gp'
            fmt=select_fdf(ROOT/'metadata/DISK.FDF',
                'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
            blank=bytes([0xe5])*fmt.image_bytes
            audit=inspect(blank,fmt,{})
            work=raw_to_dmk(blank,fmt) if native else blank
            (dest/'work-image').write_bytes(work)
            report.update(work_image_sha256=sha(work),work_image_inventory=audit)
            (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        if (dest/report['image']).read_bytes()!=data:raise ValueError('copy differs')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('cpmsim','model4','model2'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    prepare(dict(zip(('z80pack','trs80gp','trs80m2'),(a.cpmsim,a.model4,a.model2))),a.output,a.commit)
