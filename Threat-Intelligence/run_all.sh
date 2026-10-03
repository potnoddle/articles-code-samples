#!/usr/bin/env bash
# Master Execution Script for AI Threat Intelligence Suite (Dual Layout Support)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================================"
echo "  AI Threat Intelligence & Defensive Countermeasures Suite      "
echo "================================================================"

run_pillar() {
  local pillar_name="$1"
  local folder="$2"

  echo -e "\n----------------------------------------------------------------"
  echo " Running $pillar_name..."
  echo "----------------------------------------------------------------"

  if [ -f "$SCRIPT_DIR/$folder/run.sh" ]; then
    (cd "$SCRIPT_DIR/$folder" && bash run.sh)
  elif [ -f "$SCRIPT_DIR/$folder/experiment/run.sh" ]; then
    (cd "$SCRIPT_DIR/$folder/experiment" && bash run.sh)
  else
    echo "[-] Skipping $pillar_name (Runner not found)"
  fi
}

run_pillar "Pillar 1: Cyber Defense" "cyber-defense"
run_pillar "Pillar 2: Cognitive Warfare" "influence-countermeasures"
run_pillar "Pillar 3: Supply Chain Defense" "supply-chain-defense"

echo -e "\n================================================================"
echo "  [+] All Threat Intelligence verification suites complete!     "
echo "================================================================"
