#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -n "${Z80ASM:-}" ]; then
    assembler=$Z80ASM
elif command -v z80asm >/dev/null 2>&1; then
    assembler=$(command -v z80asm)
elif [ -x "$HOME/bin/z80asm" ]; then
    assembler=$HOME/bin/z80asm
else
    echo "z80asm not found; set Z80ASM or add z80asm to PATH" >&2
    exit 2
fi
mkdir -p "$root/build"
"$assembler" -fb -o"$root/build/SYSINFO.COM" "$root/src/SYSINFO.ASM"
(
    cd "$root/build"
    shasum -a 256 ../src/SYSINFO.ASM SYSINFO.COM > SHA256SUMS.txt
)
