# README.md

## File Structure
```
scraper/
├── kraken-scraper.py                     
├── README.md                      
├── .gitignore                     
└── examples/
    └── data-storage-sample/
        └── BTCUSD/
            ├── trade/
            │   └── 2025-06-12T02.jsonl
            ├── book/
            │   └── 2025-06-12T02.jsonl
            ├── ticker/
            │   └── 2025-06-12T02.jsonl
            └── ohlc/
                └── 2025-06-12T02.jsonl
```

## Gitlab Structure
```
market-logger/
    ├── .gitignore
    ├── README.md
    ├── kraken_scraper.py
    ├── requirements.txt
    ├── sanity_check.sh
    └── setup.sh
    └── examples/
        ├── data-storage-sample-v2/raw/BTCUSD
        ├── data-storage-sample/raw/BTCUSD
        └── sanity_logs/BTCUSD/                       
        │    ├── book/
        │    ├── ohlc/
        │    ├── ticker/
        │    └── trade/
        └── preTRPS-sample_output.txt

```


## Runtime logging output
```
data/
    └── raw/                       
        └── BTCUSD/
            ├── trade/
            ├── book/
            ├── ticker/
            └── ohlc/
```

## Usage
----- construction zone -----
List setup commmands here



### Branch `feature/tagging`
Implements a generic style tagging of Kraken's messages by mapping the channelID to the stream to which it is referencing. 

### Branch `feature/routing`
Using the channel map, dispatch messages to their respective parse functions based on their tagged stream type. 

### Branch `feature/store`
Condenses stream specific parse stubs into a stream_validator to verify the streams before porting onto the Pi for longterm logging.

### Branch `cleanup`
Prepares for clone to Raspberry Pi by removing debugging and validation logic, clearing out redundant comments.

### Branch `feature/live-test`
Adds a function for live testing a write to the mounted hard disk.

### Branch `error/connectClosed`
Add a top level try/except for ConnectionClosedError.
Need to write a loop that restarts the loop when the loop stops. 


### `examples/`
Includes archived `.jsonl` logs of sample data outputs from websocket test run for version-controlled data verification.


## Status
Adding the watcher loop appears to have solved the reconnection issue, been stream since last night. 
- Add logging to know exactly where errors occur, how to know where the crashes occured?
- Need to created output that verifies connection is live so i can SSH in and check. like a ping every 10 seconds or something.
- Send tails of each stream to gitlab once a day over writing yesterdays tails (automate it, just to check that every day the most recent files match the accurate timestamp)
- include a snap shot of each streams file creation for the past 24 hours
  - `sudo journalctl -u market-logger.service -f --output=cat | grep HEARTBEAT`
  - `ls /mnt/market_logs/data/raw/BTCUSD/book | tail -5`

### Metadata added per messages: 
- `recv_time`
- `channel_id`
- `stream_type`
- `pair`
- `interval` 
- `message` (raw data payload)

