#!/bin/bash
# Create fresh native-build media, then open an interactive Model 4 session.
set -euo pipefail
script_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -n ${BETTERCPM_ROOT:-} ]]; then
  root=$BETTERCPM_ROOT
elif [[ -f "$script_root/tools/build_source_disk.py" ]]; then
  root=$script_root
elif [[ -f "$PWD/tools/build_source_disk.py" ]]; then
  root=$PWD
else
  echo 'Run from the BetterCPM repository, or set BETTERCPM_ROOT to its directory.' >&2
  exit 1
fi
[[ -f "$root/tools/build_source_disk.py" ]] || { echo "Invalid BetterCPM repository: $root" >&2; exit 1; }
root=$(cd -- "$root" && pwd)
launch=yes
if [[ ${1:-} == --prepare-only ]]; then launch=no; shift; fi
out=${1:-"$root/build/native-build-$(date +%Y%m%d-%H%M%S)"}
[[ $# -le 1 ]] || { echo 'Usage: start_native_build.sh [--prepare-only] [NEW_DIRECTORY]' >&2; exit 2; }
[[ $out == /* ]] || out="$PWD/$out"
[[ ! -e $out ]] || { echo "Refusing to overwrite existing media: $out" >&2; exit 1; }
cd "$root"
# This builder first rebuilds the complete system and matching source snapshot.
python3 tools/build_source_disk.py
python3 tools/build_test_disks.py --output "$out"
cp build/trs80/BetterCPM-Build-80T-DS-800K.dmk "$out/driveb.dmk"
cp build/trs80/BetterCPM-Build-80T-DS-800K.img "$out/driveb.img"
python3 tools/prepare_native_build_session.py "$out"
cat <<EOF
Media: $out
A: boot system; B: sources/tools; C: SYSTEM work/installation disk; D: spare DATA disk.
In BetterCP/M user 0:
  B:
  SUBMIT BUILD
After SYSTEM.SYS is created and verified (the build selects C:):
  B:SYSGEN C:SYSTEM.SYS C:
C: then contains the installed system and its build files. SYSBUILD's output is
SYSTEM.SYS, not SYSGEN.SYS. Do not format C: after building.
EOF
[[ $launch == yes ]] || exit 0
emulator=${TRS80GP:-/Users/nathanael/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp}
[[ -x $emulator ]] || { echo "Set TRS80GP to the emulator executable." >&2; exit 1; }
cd "$out"
if [[ $(uname -s) == Darwin && $emulator == *.app/Contents/MacOS/* ]]; then
  # Use the normal macOS application launch path for this interactive session.
  app=${emulator%/Contents/MacOS/*}
  open -n -a "$app" --args -m4 -d0 "$out/drivea.dmk" -d1 "$out/driveb.dmk" -d2 "$out/drivec.dmk" -d3 "$out/drived.dmk"
else
  exec "$emulator" -m4 -d0 drivea.dmk -d1 driveb.dmk -d2 drivec.dmk -d3 drived.dmk
fi
