"""Measure CONFIG's 256-byte private stack through its existing machine-code tests."""
import importlib,json
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]

def main():
    peak=0;old_init=Z80.__init__;old_push=Z80.push
    def init(self,*a,**kw):old_init(self,*a,**kw);self.sp=0x4000
    def push(self,value):
        nonlocal peak
        old_push(self,value)
        if 0x3000<=self.sp<0x4000:
            peak=max(peak,0x4000-self.sp)
            assert self.sp>=0x3f00,hex(self.sp)
    Z80.__init__=init;Z80.push=push
    suites=['test_config_command_line','test_config_help','test_config_physical_cli',
            'test_config_logical_cli','test_config_edit_cli','test_config_shared_input',
            'test_config_shared_choices','test_config_startup_save',
            'test_config_saved_inspection','test_config_defaults']
    try:
        for name in suites:importlib.import_module(name).main()
    finally:Z80.__init__=old_init;Z80.push=old_push
    report=dict(status='pass',suite_names=suites,peak_bytes=peak,allocation_bytes=256,spare_bytes=256-peak)
    (ROOT/'build/config-stack.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS CONFIG stack',report)
if __name__=='__main__':main()
