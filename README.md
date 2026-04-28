# Project 19 (Variant B): Peer-to-Peer File Sharing with DHT-like Lookup

A simplified BitTorrent-style CLI system for Distributed Systems and Network Programming.

## Quick Links

- Documentation: [`docs/`](docs/)
- Demo video: [Yandex Disk](https://disk.yandex.ru/i/ShbktQh7EiTGTA)]
  
## Project Goals

- exchange files by chunks between peers
- use distributed DHT-like metadata lookup (without a central tracker)
- log join/leave and ownership changes clearly
- visualize per-peer download progress in the terminal

## Implemented Requirements

This implementation covers the main validation points of the assignment:

- complete file upload and download through chunk exchange
- peer join/leave logging
- chunk ownership registration and updates
- DHT-like lookup for file and chunk metadata
- terminal-based download progress visualization
- end-to-end integration test with multiple peers

## Architecture Summary

The project uses a layered structure:

- `domain/` contains core logic: hashing, DHT ring ownership, metadata, storage, and protocol schemas
- `application/` coordinates peer lifecycle and download orchestration
- `infrastructure/` provides TCP transport and logging adapters
- `interfaces/` contains CLI commands and terminal output

This separation keeps networking, business logic, storage, and user interaction independent enough to test and explain during the demo.

## Documentation

- Architecture overview: [`docs/architecture/overview.md`](docs/architecture/overview.md)
- Static view: [`docs/architecture/static-view.md`](docs/architecture/static-view.md)
- Dynamic view: [`docs/architecture/dynamic-view.md`](docs/architecture/dynamic-view.md)
- Deployment view: [`docs/architecture/deployment-view.md`](docs/architecture/deployment-view.md)
- Protocol: [`docs/development/protocol.md`](docs/development/protocol.md)
- Demo scenario: [`docs/development/demo.md`](docs/development/demo.md)
- Team responsibilities: [`docs/development/team-responsibilities.md`](docs/development/team-responsibilities.md)
- Limitations: [`docs/quality-assurance/limitations.md`](docs/quality-assurance/limitations.md)
- Final report: [`docs/reports/final-report.md`](docs/reports/final-report.md)

## Repository Structure

```text
.
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── docs
│   ├── architecture
│   │   ├── deployment-view.md
│   │   ├── dynamic-view.md
│   │   ├── overview.md
│   │   └── static-view.md
│   ├── assets
│   │   └── screenshots
│   │       └── user-flow
│   │           └── README.md
│   ├── development
│   │   ├── demo.md
│   │   ├── protocol.md
│   │   └── team-responsibilities.md
│   ├── quality-assurance
│   │   └── limitations.md
│   └── reports
│       └── final-report.md
├── src
│   └── p2p_share
│       ├── __init__.py
│       ├── cli.py
│       ├── application
│       │   ├── __init__.py
│       │   ├── downloader.py
│       │   └── peer.py
│       ├── domain
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── dht.py
│       │   ├── membership.py
│       │   ├── metadata.py
│       │   ├── protocol.py
│       │   └── storage.py
│       ├── infrastructure
│       │   ├── __init__.py
│       │   ├── logging_utils.py
│       │   └── network.py
│       └── interfaces
│           ├── __init__.py
│           └── cli.py
└── tests
    ├── integration
    │   └── test_upload_download.py
    └── unit
        ├── test_dht.py
        ├── test_ids.py
        ├── test_metadata.py
        └── test_storage.py
```

## Installation

### Option 1: with requirements

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

### Option 2: with pyproject extras

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Run

### Option 1: Local (single machine)

Start peer A:

```bash
p2p-peer --host 127.0.0.1 --port 9101
```

Start peer B:

```bash
p2p-peer --host 127.0.0.1 --port 9102 --bootstrap 127.0.0.1:9101
```

Start peer C:

```bash
p2p-peer --host 127.0.0.1 --port 9103 --bootstrap 127.0.0.1:9101
```

### Option 2: Multiple hosts in one LAN

On host A (bootstrap node):

```
p2p-peer --host <HOST_A_IP> --port 9101
```

On host B:

```
p2p-peer --host <HOST_B_IP> --port 9102 --bootstrap <HOST_A_IP>:9101
```

On host C:

```
p2p-peer --host <HOST_C_IP> --port 9103 --bootstrap <HOST_A_IP>:9101
```

Core commands in peer shell:

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
## Example Flow

1. Start peer A.
2. Start peer B and peer C using peer A as bootstrap.
3. Upload a file from peer A.
4. Copy the printed `file_id`.
5. Download the file from peer C.
6. Use `chunks`, `progress`, and `state` to inspect ownership and download status.

## Tests

Install development dependencies first:

```bash
pip install -e '.[dev]'
pytest
```

## Team Contributions

The project was implemented by five contributors, with responsibilities split by feature area.

| Contributor | Main responsibility | Contribution |
|---|---|---|
| d.khasanshin@innopolis.university | DHT-like lookup and membership | Implemented peer join/leave behavior, membership synchronization, ring-based lookup routing, and peer state handling. Created the basis for the README. Demonstration video editing |
| r.nasibullin@innopolis.university | Chunk storage and metadata | Implemented file splitting and reconstruction, local chunk storage, manifest handling, chunk ownership metadata, and integrity checks. |
| ro.ivanov@innopolis.university | Integration, tests, and repository cleanup | Prepared integration work, end-to-end upload/download tests, packaging configuration, repository structure cleanup. |
| n.selezenev@innopolis.university | Download orchestration and CLI demo flow | Worked on the download flow, terminal progress visibility, demo commands, and runtime behavior needed for the live user scenario. Updated the final report documentation. |
| ars.laptev@innopolis.university | Networking, protocol, and final documentation | Implemented the TCP-based message transport, JSON framing, protocol message formats, shared configuration, protocol documentation, README updates and final report documentation. |

More detailed implementation notes and functional split details are available in [`docs/development/team-responsibilities.md`](docs/development/team-responsibilities.md).
## Screenshots

The repository keeps only user-flow screenshots used in the video demo flow:
- [`docs/assets/screenshots/user-flow/`](docs/assets/screenshots/user-flow/)

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
