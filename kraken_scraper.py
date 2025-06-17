#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kraken-scraper.py - Kraken Websocket stream logger

Logs trade, book, icker, and OHLC, streams into hourly JSONL files,
with full error tracing to console and errors.log.

Gets Stream for specified SYMBOL.

Writes to specified BASEDIR.
"""
# -----------------------------------------------------------------------------
# 1. Library imports
# -----------------------------------------------------------------------------
import asyncio
from datetime import datetime, timezone
import json
import os
import traceback
import websockets

# -----------------------------------------------------------------------------
# 2. Module-level Constants
# -----------------------------------------------------------------------------
SYMBOL = "XBT/USD"                  # Kraken symbol for BTC/USD
BASE_DIR = "/mnt/market_logs/data/raw"               # Directory to store the output logs
STREAMS = [                         # Streams to subscribe to
    {"name": "trade"},
    {"name": "book", "depth": 100},
    {"name": "ticker"},
    {"name": "ohlc", "interval": 1}
]

# -----------------------------------------------------------------------------
# 3. Globals
# -----------------------------------------------------------------------------
channel_map: dict[int, dict] = {}       # Tag and Route streams

# -----------------------------------------------------------------------------
# 4. Helper Functions
# -----------------------------------------------------------------------------
def get_log_path(base_dir, pair, stream_type):
    '''
    Build and return data/raw/{pair}/{stream_type}/{YYYY-MM-DDTHH}.jsonl.
    Creates directories if required.
    '''
    hour     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H") 
    dir_path = os.path.join(base_dir, pair, stream_type)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{hour}.jsonl")

def wrap_message(recv_time: str, wall_clock: str, ch_id: int, stream_info: dict, payload: dict):
    '''
    Add metadata to raw payload for storage.
    Return wrapped message as dict.
    '''
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
    '''
    print full stacktrace on error, write to errors.log file. 
    '''
    traceback.print_exc()

    # log full stacktrace to file
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} —\n")
        traceback.print_exc(file=f)
        f.write("\n\n")



# -----------------------------------------------------------------------------
# 5. Core logic (Stream Listener)
# -----------------------------------------------------------------------------
async def log_stream():
    '''
    Connect to Kraken WS, subscribe to streams, and continuously
    receive, tag, wrap, and write messages to disk.
    '''
    url = "wss://ws.kraken.com/"  # Kraken public WebSocket endpoint

    # Reconnect Loop
    while True:
        try:
            async with websockets.connect(url) as ws:
            # Subscribe to all requested STREAMS for SYMBOL
                for sub in STREAMS:
                    await ws.send(json.dumps({
                        "event": "subscribe",
                        "pair": [SYMBOL],
                        "subscription": sub
                    }))

                # Keep listening FOREVER
                while True:
                    try:
                        raw = await ws.recv()
                        data = json.loads(raw)

                        # Handle control messages (tag channel info)
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

                        # Handle real-time data messages
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
                        print("[WARN] WebSocket closed. Reconnecting...")
                        break
                    except Exception:
                        log_error()
                        await asyncio.sleep(1)                      # pause and retry

        except Exception as e:
            log_error()
            print(f"[WARN] Cannot connect: {e!r}. Retry in 5s...")
            await asyncio.sleep(5)                                  # pause and retry


# -----------------------------------------------------------------------------
# 6. Entry Point
# -----------------------------------------------------------------------------
def main():
    '''
    Handles runtime loop and clean shutdown.
    '''
    try:
        asyncio.run(log_stream())
    except KeyboardInterrupt:
        print("\n[EXIT] Shutdown requested. Exiting cleanly...")
    except Exception as e:
        print(f"[FATAL] {e!r}")


if __name__ == "__main__":
    main()
