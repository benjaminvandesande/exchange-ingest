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

### `examples/`
Includes archived `.jsonl` logs of sample data outputs from websocket test run for version-controlled data verification.


## Status
- **Parsing dropped from logic:** no parsing required to add timestamps
- **Routing condensed:** Routing is handled within `stream_validator()` for validation of tags for log path construction.
- **Wrapper complete:** Messages are now wrapped with storage-relevant metadata.


### Metadata added per messages: 
- `recv_time`
- `channel_id`
- `stream_type`
- `pair`
- `interval` 
- `message` (raw data payload)


----

## Next Steps
- Final test using `test_write_to_disk.py`
- Do a 2 minutes test run to ensure proper logging, then cut it and push to gitlab.
- Start live storage on the Raspberry Pi 5

----

## Message Handling (Tag) 
Incoming control message format:
```json
{
    "event": "subscriptionStatus",
    "channelID": <119930881>,
    "pair":"XBT/USD",
    "subscription": {
        "name": "trade"
    }
}
```

