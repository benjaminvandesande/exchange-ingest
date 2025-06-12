# scraper.py — Refactored Kraken Scraper (Construction Zones and Logic documented inline).

import asyncio                 # For asynchronous event loop
from datetime import datetime, timezone  # For timestamped log file naming
import json                    # For parsing incoming JSON messages
import os                      # For directory and file handling
import websockets              # For WebSocket client connection


# Channel Map for tagging and routing.
channel_map = {}

# Define the minimal parsers to construct frame
def parse_trade(payload, stream_info):
    return payload

def parse_book(payload, stream_info):
    return payload

def parse_ticker(payload, stream_info):
    return payload

def parse_ohlc(payload, stream_info):
    return payload


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
    {"name": "ohlc", "interval": 1}
]

def get_log_path(stream_type):
    '''
    Helper function to build file path for log output
    '''

    # Use UTC date for organizing logs
    utc_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Create subdirectory like data/raw/XBTUSD/trade/
    dir_path = os.path.join(BASE_DIR, SYMBOL.replace("/", ""), stream_type)
    os.makedirs(dir_path, exist_ok=True)
    # Return full file path to current day’s log file
    return os.path.join(dir_path, f"{utc_date}.jsonl")

# Main async function to run WebSocket listener
async def log_stream():
    '''
    Main asynch function to run Kraken WebSocket listener.
    Runs a continuous listener for each stream declared in STREAMS.
    
    Tags each stream by its channelID, 
    enabling the separation and storage of data by stream_type.

    '''
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

        while True:                                  # While stream remains connected.
            try:                                     # keep waiting for messages.
                message = await ws.recv()            # Receive raw message
                data = json.loads(message)           # Parse JSON payload

                print("RECEIVED:", data)             # ---- Debugg print ----

                # -------------------------- Message Handling (Tag) ---------------------
                # Handle subscriptionStatus messages:
                # {"event": "subscriptionStatus",
                #  "channelID": <119930881>,
                #  "pair":"XBT/USD",
                #  "subscription": {
                #      "name":trade
                #  }
                # }
                if isinstance(data, dict) and data.get("event") == "subscriptionStatus":
                    # Store the name and interval from subscription field dict
                    sub = data.get("subscription", {})  # get {"name", "interval"} or {}.
                    channel_id = data["channelID"]      # store channelID for continuity.

                    # Standard normalization of pair name (Default to "UNKOWN").
                    pair = data.get("pair", "UKNOWN").replace("XBT", "BTC").replace("/", "")

                    #`channel_id` used to identify the stream `type` for the given `pair`
                    channel_map[channel_id] = {         # build channel_map {type, pair, interval}
                        "type": sub.get("name"),        # stream "name": trade, book, ticker, ohlc
                        "pair": pair,                   # normalized pair name. (BTCUSD)
                        "interval": sub.get("interval") # get interval from stream, default None.
                    }

                    # print channelID for stream
                    print(f"[TAGGED] {"channel_ID"}: {channel_map[channel_id]}")

                # Handle real-time data messages:
                # [channelID, payload]
                if isinstance(data, list) and isinstance(data[0], int):
                    channel_id = data[0]
                    payload = data[1]

                    recv_time = datetime.now(timezone.utc).isoformat()    # store message timestamp

                    # use the channel_map to get the stream_info
                    stream_info = channel_map.get(channel_id)
                    if not stream_info:
                        print(f"[WARN] Unknown channel ID: {channel_id}")
                        continue

                    # create stream data fields
                    stream_type = stream_info["type"]     
                    pair = stream_info["pair"]
                    interval = stream_info.get("interval")

                    print(f"[ROUTE] {stream_type.upper()} @ {pair}{f' ({interval}m)' if interval else ''}")

                # --------- Routing Block: Send to respective parser by stream_type ---------------
                if stream_type == "trade":
                    parsed = parse_trade(payload, stream_info)
                elif stream_type == "book":
                    parsed = parse_book(payload, stream_info)
                elif stream_type == "ticker":
                    parsed = parse_ticker(payload, stream_info)
                elif stream_type == "ohlc":
                    parsed = parse_ohlc(payload, stream_info)
                else:
                    print(f" [WARN] Unhandled stream type: {stream_type}")
                    parsed = payload


            # ------------------------ Error Handling -------------------------
            except json.JSONDecodeError:
                continue  # Skip malformed JSON messages

            # Prevent a full on crash, pause and reconnect.
            except Exception as e:
                # Print exception type and message for debug clarity
                print("Error:", type(e).__name__, str(e))
                await asyncio.sleep(1)  # pause, reconnecting / retrying

# Entry point — run the async listener
if __name__ == "__main__":
    asyncio.run(log_stream())
