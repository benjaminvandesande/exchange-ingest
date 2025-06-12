# scraper.py — Refactored Kraken Scraper -- Underconstruction : Storage logic.

import asyncio                 # For asynchronous event loop
from datetime import datetime, timezone  # For timestamped log file naming
import json                    # For parsing incoming JSON messages
import os                      # For directory and file handling
import websockets              # For WebSocket client connection


# Channel Map for tagging and routing.
channel_map = {}

def stream_validator(payload, stream_info):
    '''
    parser stub for validating successful routing. 
    prints a stream-specific confirmation message.
    returns payloads unchanged. 
    reference `routing-complete` tag branch on gitlab for parser stubs.
    '''

    pair = stream_info["pair"]
    interval = stream_info.get("interval")
    stream_type = stream_info["type"]

    if stream_type == "trade":
        print(f"[PARSE:TRADE] {pair} : {len(payload)} trades")
    elif stream_type == "book":
        print(f"[PARSE:BOOK] {pair} : book update")
    elif stream_type == "ticker":
        print(f"[PARSE:TICKER] {pair} : ticker update")
    elif stream_type == "ohlc":
        print(f"[PARSE:OHLC] {pair} : {interval}m candle")
    else:
        print(f" [WARN] Unhandled stream type: {stream_type}")
    
    return payload

def wrap_message(recv_time, channel_id, stream_info, payload):
    '''
    Builds the structure log message, including metadata {time, channel_id, stream_info, payload}
    '''
    return {
        "recv_time": recv_time,                  # timestamp
        "channel_id": channel_id,                # stream identifier
        "stream_type": stream_info["type"],      # the name of the stream [trade, book, ticker, ohlc]
        "pair": stream_info["pair"],             # name of the trading pair 
        "interval": stream_info.get("interval"), # the interval if any
        "message": payload,                      # raw message data
    }

# Kraken symbol format — BTC/USD is represented as XBT/USD on Kraken
SYMBOL = "XBT/USD"

# Directory to store the output logs
BASE_DIR = "data/raw"

# Define the streams to subscribe to: trades, order book, ticker
# book: depth 100 = full top-level book Kraken offers over WebSocket
STREAMS = [
    {"name": "trade"},
    {"name": "book", "depth": 100},
    {"name": "ticker"},
    {"name": "ohlc", "interval": 1}
]

def get_log_path(stream_type):
    '''
    Return full path to log file based on stream type, pair, and current UTC hour.
    Creates directories if they do not exist.
    '''
    # --------- Construction Zone: refactor for hourly file storage -------
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

                    # Announce routing to storage
                    print(f"[ROUTE] {stream_type.upper()} @ {pair}{f' ({interval}m)' if interval else ''}")
                    
                    # Validate message received and properly identified.
                    parsed = stream_validator(payload, stream_info)
                    # Pass the payload direct to the wrapper when streams are valid
                
                    wrapped = wrap_message(recv_time, channel_id, stream_info, parsed)      # swap param parsed, for payload when slimming code.


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
