#!/bin/zsh
set -eu
task_root="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$task_root/tools/launch_cromemco.py" \
  --image-dir "$task_root/build/cromemco-engineering/profiles/cromemco-fullram/cromemco/build/cromemco" \
  --simulator "$task_root/build/cromemco-emulator-final/cromemcosim/cromemcosim"
