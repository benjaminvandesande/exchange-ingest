# kraken-scraper.py - Kraken Stream Logger (Hourly JSONL, Stream-Separated).
# Logging streams: {trade, book-100, ticker, ohlc-1m}

import asyncio                 # For asynchronous event loop
from datetime import datetime, timezone  # For timestamped log file naming
import json                    # For parsing incoming JSON messages
import os                      # For directory and file handling
import websockets              # For WebSocket client connection


# Channel Map for tagging and routing.
channel_map = {}

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
        "message": payload,                      # unparsed message payload
    }

# Kraken symbol format — BTC/USD is represented as XBT/USD on Kraken
SYMBOL = "XBT/USD"

# Directory to store the output logs
BASE_DIR = "data/raw"

# Streams to subscribe to - trade, book (depth-100), tiker, and 1m ohlc candles.
STREAMS = [
    {"name": "trade"},
    {"name": "book", "depth": 100},
    {"name": "ticker"},
    {"name": "ohlc", "interval": 1}
]

def get_log_path(base_dir, pair, stream_type):
    '''
    Return full path to log file based on stream type, pair, and current UTC hour.
    Creates directories if they do not exist.
    '''

    # Use UTC date and hour for organizing logs 
    hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H") 
    # Create subdirectory data/raw/pair/stream_type/
    dir_path = os.path.join(base_dir, pair, stream_type)
    os.makedirs(dir_path, exist_ok=True)

    # Return the file path with the hour appended.
    return os.path.join(dir_path, f"{hour}.jsonl")

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

                # Handle control messages (tag channel info)
                if isinstance(data, dict) and data.get("event") == "subscriptionStatus":
                    sub = data.get("subscription", {})
                    channel_id = data["channelID"]
                    pair = data.get("pair", "UKNOWN").replace("XBT", "BTC").replace("/", "")
                    channel_map[channel_id] = {
                        "type": sub.get("name"),        
                        "pair": pair,                   
                        "interval": sub.get("interval") 
                    }

                # Handle real-time data messages
                if isinstance(data, list) and isinstance(data[0], int):
                    # Extract core variables
                    channel_id = data[0]
                    payload = data[1]
                    recv_time = datetime.now(timezone.utc).isoformat()
                    stream_info = channel_map.get(channel_id)

                    # Wrap with metadata for storage
                    wrapped = wrap_message(recv_time, channel_id, stream_info, payload)

                    # Generate the storage file path for the message
                    file_path = get_log_path(BASE_DIR, stream_info["pair"], stream_info["type"])
                    with open(file_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(wrapped) + "\n")

            # ------------------------ Error Handling -------------------------
            except json.JSONDecodeError:
                continue  # Skip malformed JSON messages

            # Prevent a full on crash, pause and reconnect.
            except Exception as e:
                # Print exception type and message for debug clarity
                print("Error:", type(e).__name__, str(e))
                await asyncio.sleep(1)  # pause, reconnecting / retrying

def main():
    '''
    Entry point for Kraken stream logger.
    Handles runtime loop and clean shutdown.
    '''
    try:
        asyncio.run(log_stream())
    except KeyboardInterrupt:
        print("\n[EXIT] Shutdown requested. Exiting cleanly...")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
