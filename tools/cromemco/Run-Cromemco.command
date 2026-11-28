#!/bin/zsh
set -eu
bundle_root="$(cd "$(dirname "$0")" && pwd)"
sim="$bundle_root/Host/prebuilt/macos-arm64/cromemcosim"
if [[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 && -x "$sim" && $# == 0 ]]; then
  session="$bundle_root/Session"
  mkdir -p "$session/disks"
  for entry in a:System b:Work c:Utilities-1 d:Utilities-2; do
    drive="${entry%%:*}"
    volume="${entry#*:}"
    if [[ ! -f "$session/disks/drive${drive}.dsk" ]]; then
      cp "$bundle_root/Media/BetterCPM-1.3-Cromemco-${volume}.dsk" "$session/disks/drive${drive}.dsk"
    fi
  done
  print -rl -- drivea.dsk driveb.dsk drivec.dsk drived.dsk > "$session/disks/disk.map"
  cp "$bundle_root/Media/system.conf" "$session/system.conf"
  print -r -- "Writable session: $session"
  cd "$session"
  exec "$sim" -z -R -M1 -f0 -r "$bundle_root/Host/roms" -c "$session/system.conf" -d "$session/disks"
fi
exec python3 "$bundle_root/Run-Cromemco.py" "$@"
