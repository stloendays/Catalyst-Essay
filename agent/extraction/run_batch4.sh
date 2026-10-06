#!/usr/bin/env bash
# Batch 4 extraction (2026-10-06): the 21 new papers, four passes, in groups that run in parallel.
# usage: bash run_batch4.sh <group-name> <doi> [<doi> ...]
set -u
cd "$(dirname "$0")"
PY=/d/Research/CatalystForge/.venv/Scripts/python.exe
g=$1; shift
args=(); for d in "$@"; do args+=(--doi "$d"); done
for p in main figures si si_figures; do
  PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 "$PY" extract_records.py --api-yes --pass "$p" \
    --token-cap 9000000 --pass-cap 3600000 "${args[@]}" >> "out/b${BATCH:-4}_${g}.log" 2>&1
done
echo "DONE $g" >> "out/b${BATCH:-4}_${g}.log"
