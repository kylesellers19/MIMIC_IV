#!/bin/zsh
# run_2026-11-10 — the only way this run pushes. Runs the push gate on the unpushed range and pushes the
# branch ONLY when the gate itself exits 0. The gate's output is shown in full; nothing is piped, so no
# other command's exit status can stand in for the gate's (see BLOCKERS.md, INCIDENT I-01).
cd "$(dirname "$0")/.."
git fetch -q origin || { echo "fetch failed — not pushing"; exit 2; }
zsh scripts/run0919_env.sh scripts/run1110_push_gate.py
rc=$?
if [ $rc -ne 0 ]; then
  echo "gate exit $rc — NOT pushing; commits stay local"
  exit 1
fi
git push origin run/2026-09-19
