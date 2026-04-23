# Project 19 (Variant B): Simplified BitTorrent with DHT-like Peer Discovery

A CLI-based peer-to-peer file sharing system for a Distributed Systems and Network Programming course.

The project implements a simplified BitTorrent-style flow:
- peers join and leave a network
- files are split into chunks
- file metadata and chunk ownership are placed on a hash ring
- chunk owners are resolved through DHT-like lookup and message forwarding
- peers exchange chunks and reconstruct complete files
- download progress is visualized in terminal output

## Features

- Peer startup and TCP server per node
- Peer join and leave with event logs
- Membership synchronization using bootstrap and state sync messages
- DHT-like key placement on a ring using hashed peer IDs and hashed file/chunk IDs
- Metadata registration for files and chunk ownership
- Distributed lookup for file manifests and chunk owners
- Chunk transfer via framed JSON messages and Base64 payloads
- Integrity checks for chunks and reconstructed files
- Per-peer progress display during download
- CLI commands for demo and inspection

## Architecture Overview

Main modules:
- `network.py`: framed JSON TCP RPC
- `protocol.py`: message and schema types
- `dht.py`: hash ring and ownership mapping
- `membership.py`: known peers and sync
- `metadata.py`: file and chunk owner indexes
- `storage.py`: chunk split/store/reconstruct
- `peer.py`: node lifecycle and message handlers
- `downloader.py`: download orchestration and progress
- `cli.py`: interactive peer shell

Detailed design is in [docs/architecture.md](docs/architecture.md).

## Repository Structure

```text
.
├── README.md
├── pyproject.toml
├── docs
│   ├── architecture.md
│   ├── demo.md
│   ├── limitations.md
│   ├── protocol.md
│   ├── report.md
│   └── team_split.md
├── src
│   └── p2p_share
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── dht.py
│       ├── downloader.py
│       ├── logging_utils.py
│       ├── membership.py
│       ├── metadata.py
│       ├── network.py
│       ├── peer.py
│       ├── protocol.py
│       └── storage.py
└── tests
    ├── test_dht.py
    ├── test_ids.py
    ├── test_integration_e2e.py
    ├── test_metadata.py
    └── test_storage.py
```

## Setup

Requirements:
- Python 3.11+

Install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run Peers

Start peer A:

```bash
p2p-peer --host 127.0.0.1 --port 9101
```

Start peer B and join A:

```bash
p2p-peer --host 127.0.0.1 --port 9102 --bootstrap 127.0.0.1:9101
```

Start peer C and join A:

```bash
p2p-peer --host 127.0.0.1 --port 9103 --bootstrap 127.0.0.1:9101
```

## CLI Commands

Inside a peer shell:

```text
help
join <host:port>
upload <path>
download <file_id> [destination]
peers
files
lookup <file_id>
chunks <file_id>
progress
state
leave
exit
```

## Upload and Download Example

On peer A:

```text
upload ./sample.txt
```

Copy printed `file_id`.

On peer C:

```text
download <file_id> ./downloaded_sample.txt
```

Then inspect chunk ownership and progress:

```text
chunks <file_id>
progress
```

## Run Tests

```bash
pytest
```

## Demo Walkthrough

A full 3-peer live demo script is documented in [docs/demo.md](docs/demo.md).
