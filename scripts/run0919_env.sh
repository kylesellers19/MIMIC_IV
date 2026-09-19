#!/bin/zsh
# run_2026-09-19 — launch a Python script with the environment the modeling phases need.
# LightGBM/XGBoost wheels need libomp; the copy bundled with torch is used (no system install).
cd "$(dirname "$0")/.."
export DYLD_LIBRARY_PATH="$PWD/.venv/lib/python3.14/site-packages/torch/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
export HF_HUB_DISABLE_TELEMETRY=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python "$@"
