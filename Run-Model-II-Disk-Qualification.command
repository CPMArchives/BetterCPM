#!/bin/zsh
set -eu
cd "${0:A:h}"
exec python3 -B tools/run_model2_install.py "$@"
