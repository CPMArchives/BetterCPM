#!/bin/bash
# Launch the extracted release candidates. Quit trs80gp before replacing images.
set -eu

releases="${BETTERCPM_RELEASES:-$HOME/Downloads/BetterCPM/Releases}"
emulator="${TRS80GP:-$HOME/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp}"
system="$releases/BetterCPM-1.0-System-Model4-candidate/images"
utilities="$releases/BetterCPM-Utilities-1.0-Model4-candidate/images/Model4"
images=(
  "$system/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk"
  "$utilities/BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk"
  "$utilities/BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk"
  "$system/BetterCPM-Work-800K.dmk"
)

if [[ ! -x "$emulator" ]]; then
  printf 'Cannot execute trs80gp: %s\nSet TRS80GP to its executable path.\n' "$emulator" >&2
  exit 1
fi
for image in "${images[@]}"; do
  if [[ ! -f "$image" ]]; then
    printf 'Missing disk image: %s\n' "$image" >&2
    exit 1
  fi
done

if [[ "${1:-}" == "--check" ]]; then
  printf 'Emulator: %s\n' "$emulator"
  printf 'A: %s\nB: %s\nC: %s\nD: %s\n' "${images[@]}"
  exit 0
fi
if [[ $# -ne 0 ]]; then
  printf 'Usage: %s [--check]\n' "$0" >&2
  exit 1
fi

exec "$emulator" -m4 -d0 "${images[0]}" -d1 "${images[1]}" -d2 "${images[2]}" -d3 "${images[3]}"
