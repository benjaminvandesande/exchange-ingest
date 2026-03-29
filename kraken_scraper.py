#!/usr/bin/env python3
"""
Kraken WebSocket stream logger.

Subscribes to configured Kraken market data streams for a single symbol,
wraps each message with minimal metadata, and writes hourly JSONL logs
to disk for downstream ETL and experiments.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
import traceback

import websockets

SYMBOL = "XBT/USD"
BASE_DIR = "/mnt/market_logs/data/raw"
STREAMS = [
    {"name": "trade"},
    {"name": "book", "depth": 100},
    {"name": "ticker"},
    {"name": "ohlc", "interval": 1}
]

channel_map: dict[int, dict] = {}

def get_log_path(base_dir, pair, stream_type):
    """Return the hourly JSONL path for a stream and create directories if needed."""
    hour     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H") 
    dir_path = os.path.join(base_dir, pair, stream_type)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{hour}.jsonl")

def wrap_message(recv_time: str, wall_clock: str, ch_id: int, stream_info: dict, payload: dict):
    """Wrap a raw exchange payload with metadata."""
    return {
        "recv_time":    recv_time,
        "wall_clock":   wall_clock,
        "channel_id":   ch_id,
        "stream_type":  stream_info["type"],
        "pair":         stream_info["pair"], 
        "interval":     stream_info.get("interval"),
        "message":      payload,
    }

def log_error():
    """Print the current stack trace and append it to errors.log."""
    traceback.print_exc()
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} —\n")
        traceback.print_exc(file=f)
        f.write("\n\n")

# Core logic (Stream Listener)
async def log_stream():
    """Connect to Kraken, subscribe to streams, and write messages to disk."""
    url = "wss://ws.kraken.com/"
    while True:
        print("[INFO] open websocket.", flush=True)
        try:
            async with websockets.connect(url) as ws:
                print("[INFO] connected.", flush=True)
                # Subscribe to all requested STREAMS for SYMBOL
                for sub in STREAMS:
                    await ws.send(json.dumps({
                        "event": "subscribe",
                        "pair": [SYMBOL],
                        "subscription": sub,
                    }))

                # Keep listening FOREVER
                while True:
                    try:
                        raw = await ws.recv()
                        data = json.loads(raw)

                        # Control messages (tag channel info)
                        if isinstance(data, dict) and data.get("event") == "subscriptionStatus":
                            ch_id   = data["channelID"]
                            sub     = data["subscription"]
                            pair    = data.get("pair", "").replace("XBT", "BTC").replace("/", "")
                            channel_map[ch_id] = {
                                "type":     sub["name"],        
                                "pair":     pair,                   
                                "interval": sub.get("interval") 
                            }
                            continue

                        # Data messages
                        if isinstance(data, list) and isinstance(data[0], int):
                            # Extract core variables
                            ch_id       = data[0]
                            payload     = data[1]
                            stream_info = channel_map.get(ch_id)
                            if not stream_info:
                                # unknown channel - skip
                                continue

                            recv_time = datetime.now(timezone.utc).isoformat()
                            wall_clock = datetime.now().astimezone().isoformat()
                            wrapped   = wrap_message(recv_time, wall_clock, ch_id, stream_info, payload)
                            path      = get_log_path(BASE_DIR, stream_info["pair"], stream_info["type"])
                            with open(path, "a", encoding="utf-8") as f:
                                f.write(json.dumps(wrapped) + "\n")

                    except json.JSONDecodeError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        print("[WARNING] WebSocket connnection closed, reconnecting.")
                        break
                    except Exception:
                        log_error()
                        await asyncio.sleep(1)                      # pause and retry

        except Exception as e:
            log_error()
            print(f"[WARNING] Cannot connect: {e!r}. Retry in 5 seconds.")
            await asyncio.sleep(5)                                  # pause and retry


def main():
    """Run the logger until interrupted."""
    try:
        asyncio.run(log_stream())
    except KeyboardInterrupt:
        print("\n[INFO] Shutdown requested.")
    except Exception as e:
        print(f"[ERROR] {e!r}")

if __name__ == "__main__":
    main()
