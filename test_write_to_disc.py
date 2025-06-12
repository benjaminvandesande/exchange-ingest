# test_write_to_disc.py     Sanity check before running 24/7 scraper
# Verify: proper mountpath, write access permissions granted, file io behaves as expected on linux.

import os
import json
from datetime import datetime, timezone

# Set to match base dir on the pi
BASE_DIR = "/mnt/storage/data/raw"

def test_disk_write():
    '''
    Disk write test to ensure proper scraper logging.
    Gather "live-sample" from the scraper for data versioning update.
    '''
    pair = "BTCUSD"
    stream_type = "test"
    hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    dir_path = os.path.join(BASE_DIR, pair, stream_type)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{hour}.jsonl")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"test": "write", "time": hour}) + "\n")

    print(f"[OK] Test log written to: {file_path}")

if __name__ == "__main__":
    test_disk_write()