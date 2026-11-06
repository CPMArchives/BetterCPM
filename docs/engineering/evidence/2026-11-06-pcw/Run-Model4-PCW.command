#!/bin/zsh
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
repo_dir="${0:A:h}/../../../.."
repo_dir="${repo_dir:A}"
work_dir="${repo_dir:h}"
system_image="${PCW_SYSTEM_IMAGE:-$work_dir/../release-promotion-20261104/final-systems/trs80gp/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk}"
simulator="${PCW_SIMULATOR:-$HOME/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp}"
cd "$repo_dir"
mkdir -p "$work_dir/results"
run_dir=$(mktemp -d "$work_dir/results/model4.XXXXXX")
echo "Checking the PCW image. Results will be in $run_dir."
/usr/bin/caffeinate -i python3 -B docs/engineering/evidence/2026-11-05-cpc/qualify.py \
  --manifest docs/engineering/evidence/2026-11-06-pcw/samples.json \
  --target trs80gp --system "$system_image" --simulator "$simulator" \
  --images "$work_dir/images" --output "$run_dir/evidence" --jobs 2 \
  2>&1 | tee "$run_dir/console.log"
