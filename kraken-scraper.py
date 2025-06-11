# scraper.py — Clean Kraken Scraper (Documented Line by Line)

import asyncio                 # For asynchronous event loop
import websockets              # For WebSocket client connection
import json                    # For parsing incoming JSON messages
import os                      # For directory and file handling
from datetime import datetime, timezone  # For timestamped log file naming

# Kraken symbol format — BTC/USD is represented as XBT/USD on Kraken
SYMBOL = "XBT/USD"

# Directory to store the output logs
BASE_DIR = "data/raw"

# Define the streams to subscribe to: trades, order book, ticker
# book: depth 100 = full top-level book Kraken offers over WebSocket
STREAMS = [
    {"name": "trade"},
    {"name": "book", "depth": 100},
    {"name": "ticker"}
]

# Helper function to build file path for log output
def get_log_path(stream_type):
    # Use UTC date for organizing logs
    utc_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Create subdirectory like data/raw/XBTUSD/trade/
    dir_path = os.path.join(BASE_DIR, SYMBOL.replace("/", ""), stream_type)
    os.makedirs(dir_path, exist_ok=True)
    # Return full file path to current day’s log file
    return os.path.join(dir_path, f"{utc_date}.jsonl")

# Main async function to run WebSocket listener
async def log_stream():
    url = "wss://ws.kraken.com/"  # Kraken public WebSocket endpoint

    async with websockets.connect(url) as ws:
        print(f"Connected to Kraken for {SYMBOL}")

        # Subscribe to all requested streams for the given symbol
        for stream in STREAMS:
            sub_msg = {
                "event": "subscribe",
                "pair": [SYMBOL],
                "subscription": stream
            }
            await ws.send(json.dumps(sub_msg))  # Send subscription as JSON

        while True:
            try:
                message = await ws.recv()            # Receive raw message
                data = json.loads(message)           # Parse JSON payload

                print("RECEIVED:", data)             # ---- Debugg print ----


                # Skip system-level messages like event confirmations or heartbeats
                if isinstance(data, dict) and "event" in data:
                    continue

                # Handle actual data messages: [channelID, payload, metadata]
                if isinstance(data, list) and len(data) >= 3:
                    #_, payload, meta = data         # Unpack message fields
                    # --- comment out, trouble shoot unpack 3 error. ----
                    if len(data) == 3:              # unpack message: 3 fields
                        _, payload, meta = data     
                    elif len(data) == 2:            # unpack message: 2 fields
                        _, payload = data
                        meta = {}
                    else:                           # skip malformed messages
                        continue                    


                    if isinstance(meta, dict):
                        stream_type = meta.get("channelName", "unknown")
                        path = get_log_path(stream_type)  # Build path to log file

                        # Append raw payload to corresponding .jsonl log file
                        with open(path, "a") as f:
                            f.write(json.dumps(payload) + "\n")

            except json.JSONDecodeError:
                continue  # Skip malformed JSON messages silently

            except Exception as e:
                # Print exception type and message for debug clarity
                print("Error:", type(e).__name__, str(e))
                await asyncio.sleep(1)  # Brief pause before reconnecting or retrying

# Entry point — run the async listener
if __name__ == "__main__":
    asyncio.run(log_stream())
