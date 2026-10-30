#!/bin/bash
# Mount the extracted release candidates, then preserve those mounts at launch.
set -eu

releases="${BETTERCPM_RELEASES:-$HOME/Downloads/BetterCPM/Releases}"
bcpm="${BCPM:-$HOME/scripts/bcpm}"
system="$releases/BetterCPM-1.0-System-cpmsim-candidate/images"
utilities="$releases/BetterCPM-Utilities-1.0-cpmsim-candidate/images/cpmsim"
images=(
  "$system/BetterCPM-Distribution-z80pack-332K.dsk"
  "$utilities/BetterCPM-Utilities-z80pack-332K.dsk"
  "$utilities/BetterCPM-NOAH-z80pack-332K.dsk"
  "$system/BetterCPM-Work-332K.dsk"
)

if [[ ! -x "$bcpm" ]]; then
  printf 'Cannot execute bcpm: %s\nSet BCPM to its executable path.\n' "$bcpm" >&2
  exit 1
fi
for image in "${images[@]}"; do
  if [[ ! -f "$image" ]]; then
    printf 'Missing disk image: %s\n' "$image" >&2
    exit 1
  fi
done

if [[ "${1:-}" == "--check" ]]; then
  printf 'bcpm: %s\n' "$bcpm"
  printf 'A: %s\nB: %s\nC: %s\nD: %s\n' "${images[@]}"
  exit 0
fi
if [[ $# -ne 0 ]]; then
  printf 'Usage: %s [--check]\n' "$0" >&2
  exit 1
fi

"$bcpm" mount a "${images[0]}"
"$bcpm" mount b "${images[1]}"
"$bcpm" mount c "${images[2]}"
"$bcpm" mount d "${images[3]}"
exec "$bcpm" z /usecurrent
