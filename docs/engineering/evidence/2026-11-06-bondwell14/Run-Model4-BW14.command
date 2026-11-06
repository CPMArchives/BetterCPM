#!/bin/zsh
set -euo pipefail
here="${0:A:h}"
repo="${here:h:h:h:h}"
cd "$repo"
images="${BW14_IMAGES:-$repo/../bw14-originals}"
system_image="${BW14_SYSTEM:-$repo/../../release-promotion-20261104/final-systems/trs80gp/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk}"
simulator="${BW14_SIMULATOR:-$HOME/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp}"
cpmtools="${BW14_CPMTOOLS:-$repo/../../post-1.0-model2-formats/cpmtools-posix}"
mapper="${BW14_MAPPER:-$repo/build/rsx/FDF.RSX}"
jobs="${BW14_JOBS:-9}"
# The runner creates this fresh directory; mktemp reserves a unique parent.
mkdir -p "$repo/build"
run_parent=$(mktemp -d "$repo/build/bw14-model4.XXXXXX")
output="$run_parent/evidence"
print -r -- "BW14 parallel batch: $output"
python3 -B "$here/model4.py" --prepare --images "$images" --output "$output" \
  --system "$system_image" --mapper "$mapper" --cpmtools "$cpmtools" --jobs "$jobs"
python3 -B "$here/model4.py" --images "$images" --output "$output" \
  --simulator "$simulator" --cpmtools "$cpmtools" --jobs "$jobs" 2>&1 | tee "$run_parent/console.log"
print -r -- "Completed: $output/results.json"
