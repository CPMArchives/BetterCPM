#!/usr/bin/env python3
"""Check the actual UART stdio reader with deliberately poisoned stack locals."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--expect-bug', action='store_true')
    args = parser.parse_args()
    source = (args.source_root / 'iodevices/cromemco-hal.c').read_text()
    start = source.index('static int stdio_in(int dev)')
    end = source.index('static void stdio_out(', start)
    function = source[start:end]
    wrapper = '''#include <stdio.h>
#include <unistd.h>
#include <poll.h>
#include <stdlib.h>
typedef unsigned char BYTE;
#define UNUSED(x) (void)(x)
#define LOGE(...) ((void)0)
static void set_unix_terminal(void) {}
'''+function+'''
int main(int argc, char **argv) {
    (void)argc;
    int actual = stdio_in(0), expected = atoi(argv[1]);
    printf("expected=%d actual=%d\\n", expected, actual);
    return actual == expected ? 0 : 1;
}
'''
    with tempfile.TemporaryDirectory(prefix='cromemco-uart-') as temporary:
        root = Path(temporary)
        (root/'reader.c').write_text(wrapper)
        subprocess.run(['cc','-std=c99','-O0','-ftrivial-auto-var-init=pattern',
                        str(root/'reader.c'),'-o',str(root/'reader')],check=True)
        results = [subprocess.run([str(root/'reader'),str(value)],input=bytes([value]),
                                  stdout=subprocess.PIPE) for value in (0,65,97,127,255)]
        for result in results:
            print(result.stdout.decode().strip())
        if args.expect_bug:
            assert all(result.returncode == 1 for result in results), 'original bug was not reproduced'
            print('PASS: original reader reproducibly discards valid characters')
        else:
            assert all(result.returncode == 0 for result in results), 'UART reader corrupted an input byte'
            print('PASS: UART input survives poisoned host stack for all tested byte values')


if __name__ == '__main__':
    main()
