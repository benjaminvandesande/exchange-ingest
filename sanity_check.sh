#!/usr/bin/env bash
set -euo pipefail

# Adjust these if needed
SCRAPER_PATH="./kraken_scraper.py"
BASE_DIR="examples/sanity_check.sh-test"
PAIR="BTCUSD"
STREAMS=("trade" "book" "ticker" "ohlc")

# 1) Start the scraper in the background
python3 "$SCRAPER_PATH" &
PID=$!

# 2) Let it run briefly to give a chance to connect and get at least 1 message
sleep 5

# 3) Stop it after 1 second of data is logged
kill $PID 2>/dev/null || true

# 4) Verify writes by reconstructing file path and checking if the file exists
echo
echo "===== Sanity Check Results ====="
for stream in "${STREAMS[@]}"; do
  FILE="$BASE_DIR/$PAIR/$stream/$(date -u +%Y-%m-%dT%H).jsonl"
  if [[ -f "$FILE" ]]; then
    echo
    echo "[OK] Stream: $stream"
    echo "------ Last 3 lines of $FILE ------"
    tail -n 3 "$FILE"
  else
    echo
    echo "[FAIL] Stream: $stream — File not found: $FILE"
  fi
done
echo