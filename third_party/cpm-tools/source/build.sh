#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$root/sysinfo/build.sh"
"$root/diskinfo/build.sh"
"$root/dpbchk/build.sh"
"$root/fsck/build.sh"
"$root/diskedit/build.sh"
"$root/cominfo/build.sh"
"$root/bdosprobe/build.sh"
python3 "$root/tools/build_tools_image.py"
