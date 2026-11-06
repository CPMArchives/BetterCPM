"""Prepare private qualification media from a baseline System and rebuilt RAM carriers."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import sha256
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
from fdf_v1 import parse,serialize

def main():
    p=ArgumentParser(description=__doc__)
    for name in ('base-system','runtime-build','catalogue','config','cpmtools','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    for name in ('base_system','runtime_build','catalogue','config','cpmtools'):setattr(a,name,getattr(a,name).resolve(strict=True))
    a.output=a.output.resolve();a.output.mkdir(parents=True)
    fmt=select_fdf(ROOT/'metadata/DISK.FDF','MMF017')
    baseline=a.base_system.read_bytes();carrier=(a.runtime_build/'disks/drivea.dsk').read_bytes()
    assert len(baseline)==len(carrier)==fmt.image_bytes
    image=a.output/'system.dsk';at=fmt.reserved_records*128
    image.write_bytes(carrier[:at]+baseline[at:])
    (a.output/'diskdefs').write_text(disk_definition(fmt))
    database=a.output/'DISK.FDB';database.write_bytes(serialize(parse(a.catalogue.read_text())))
    for name,path in [('CONFIG.COM',a.config),('DISK.FDB',database)]:
        subprocess.run([str(a.cpmtools/'cpmrm'),'-f','bettercpm-default',str(image),'0:'+name],cwd=a.output,check=True)
        subprocess.run([str(a.cpmtools/'cpmcp'),'-f','bettercpm-default',str(image),str(path),'0:'+name],cwd=a.output,check=True)
    digest=lambda b:sha256(b).hexdigest()
    (a.output/'preparation.json').write_text(json.dumps(dict(baseline_sha256=digest(baseline),runtime_carrier_sha256=digest(carrier),
        resident_sha256=digest((a.runtime_build/'resident.bin').read_bytes()),config_sha256=digest(a.config.read_bytes()),
        catalogue_sha256=digest(database.read_bytes()),system_sha256=digest(image.read_bytes()),reserved_bytes_replaced=at),indent=2)+'\n')
    print(image)
if __name__=='__main__':main()
