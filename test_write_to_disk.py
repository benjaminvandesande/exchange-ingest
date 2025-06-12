#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_write_to_disk.py - Sanity check before running 24/7 scraper

Verifies that the mount path exists, write permissions are in place, 
and basic file I/O behaves as expected on Raspberry Pi. 
"""
import os
import json
from datetime import datetime, timezone

# Set to match base dir on the pi
BASE_DIR = "examples/test_disk_write/result"
PAIR     = "BTCUSD"
STREAMS  = ["trade", "book", "ticker", "ohlc"]


def test_disk_write():
    """
    Write single JSONL line under {BASE_DIR}/BTCUSD/test/{YYYY-MM-DDTHH}.jsonl 
    to confirm permission, path, and encoding.
    """
    pair        = "BTCUSD"
    stream_type = "test"
    hour        = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    dir_path = os.path.join(BASE_DIR, pair, stream_type)
    os.makedirs(dir_path, exist_ok=True)

    path = os.path.join(dir_path, f"{hour}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        payload = {"test": "write", "time": hour}
        f.write(json.dumps(payload) + "\n")

    print(f"[OK] Test log written to: {path}")

if __name__ == "__main__":
    test_disk_write()
