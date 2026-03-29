# exchange-ingest

## Overview
This repository is the ingestion/capture component used in my research infrastructure. It connects to Kraken's public WebSocket feeds, subscribes to configured streams, minimally annotates each message, and writes raw structured data to disk for downstream ETL and experiments. It is not a backfill service or a data-cleaning/analytics pipeline.

## Data and usage note
This repository does not include captured market data. Kraken market data used in this research was collected with permission for research purposes. If collected data or derivative use is later commercialized or monetized, Kraken may require additional notice or separate permission. Users are responsible for reviewing the applicable terms for their own use case.

## High-level data flow
1. Connect to Kraken's public WebSocket endpoint.
2. Subscribe to the configured streams for `SYMBOL`.
3. Map Kraken channel IDs to stream metadata from subscription status messages.
4. For each data message, wrap the payload with minimal metadata and append to an hourly JSONL file.

## Outputs
Default output root is `BASE_DIR=/mnt/market_logs/data/raw` (configurable in `kraken_scraper.py`).

Directory layout:
```
BASE_DIR/
  BTCUSD/
    trade/
      2025-06-12T02.jsonl
    book/
      2025-06-12T02.jsonl
    ticker/
      2025-06-12T02.jsonl
    ohlc/
      2025-06-12T02.jsonl
```

File format:
- Each line is a standalone JSON object (JSONL).
- Fields added by the logger:
  - `recv_time` (UTC ISO timestamp)
  - `wall_clock` (local ISO timestamp)
  - `channel_id`
  - `stream_type`
  - `pair` (e.g., `BTCUSD` derived from Kraken `XBT/USD`)
  - `interval` (only present for interval streams, e.g., OHLC)
  - `message` (raw payload from Kraken)

## Setup & Run
Minimal install and run:
```
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 kraken_scraper.py
```

Alternatively, run:
```
./setup.sh
./venv/bin/python3 kraken_scraper.py
```

Ensure `BASE_DIR` is writable by the current user. 

The script will create the pair/stream subdirectories as needed, but it cannot create parent directories in locations where the user lacks permission.

## Raspberry Pi + systemd
The file `market-logger.service.example` is a template systemd unit used on a headless Raspberry Pi. To use it:
1. Copy it to `/etc/systemd/system/market-logger.service`.
2. Update `User`, `WorkingDirectory`, and `ExecStart` for your environment.
3. Reload and start the service:
```
sudo systemctl daemon-reload
sudo systemctl enable --now market-logger.service
```
To tail logs:
```
journalctl -u market-logger.service -f
```

## Configuration
Edit constants in `kraken_scraper.py`:
- `SYMBOL`: Kraken pair symbol (default `XBT/USD`).
- `BASE_DIR`: Output root directory (default `/mnt/market_logs/data/raw`).
- `STREAMS`: List of Kraken subscription objects (default: trade, book depth 100, ticker, ohlc interval 1).

Notes:
- Output `pair` is derived from Kraken subscription status messages by replacing `XBT` with `BTC` and removing `/`.
- The script creates stream subdirectories on write if they do not exist.

## Operational notes
- Hourly file rotation is based on current UTC time at write time.
- Errors are printed to stderr and appended to `errors.log` in the working directory.
- `sanity_check.sh` runs the scraper briefly, then checks for newly written files under the configured `BASE_DIR`.

## Limitations / non-goals
- No data validation beyond minimal tagging.
- No backfill, deduplication, or schema normalization.
- No compression, retention policy, or file lifecycle management.
- No metrics, health checks, or heartbeat beyond stdout/stderr logs.
- No CLI or config file; configuration is via constants in code.

## Relationship to downstream repos and the paper
This repo produces raw ingestion data used by downstream ETL/feature pipelines in `market-pipe` and modeling workflows in `simple-model`. Those downstream repos (and the paper that references them) are separate and are not required to run this logger.
