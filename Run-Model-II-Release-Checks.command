#!/bin/zsh
set -eu
cd "${0:A:h}"
exec python3 -B tools/qualify_model2_release_media.py "$@"
