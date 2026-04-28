# Project 19 (Variant B): P2P File Sharing with DHT-like Lookup

A simplified BitTorrent-style CLI system for Distributed Systems and Network Programming.

## Quick Links

- Documentation: [`docs/`](docs/)
- Demo scenario: [`docs/development/demo.md`](docs/development/demo.md)
- Final report: [`docs/reports/final-report.md`](docs/reports/final-report.md)

## Project Goals

- exchange files by chunks between peers
- use distributed DHT-like metadata lookup (without a central tracker)
- log join/leave and ownership changes clearly
- visualize per-peer download progress in terminal

## Architecture Summary

The codebase is structured into clear layers:

- `domain/` for hashing, ring ownership, metadata, storage, protocol schemas
- `application/` for peer lifecycle and download orchestration
- `infrastructure/` for TCP transport and logging adapters
- `interfaces/` for CLI commands and terminal output

Detailed architecture documents:
- [`docs/architecture/overview.md`](docs/architecture/overview.md)
- [`docs/architecture/static-view.md`](docs/architecture/static-view.md)
- [`docs/architecture/dynamic-view.md`](docs/architecture/dynamic-view.md)
- [`docs/architecture/deployment-view.md`](docs/architecture/deployment-view.md)

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

## Tests

```bash
pytest
```

## Team

Contributors:
- d.khasanshin@innopolis.university
- r.nasibullin@innopolis.university
- ro.ivanov@innopolis.university
- n.selezenev@innopolis.university
- ars.laptev@innopolis.university

Branch-to-owner mapping:
- Branch 1: ars.laptev@innopolis.university
- Branch 2: d.khasanshin@innopolis.university
- Branch 3: r.nasibullin@innopolis.university
- Branch 4: n.selezenev@innopolis.university
- Branch 5: ro.ivanov@innopolis.university

Functional split details are in [`docs/development/team-responsibilities.md`](docs/development/team-responsibilities.md).

## Screenshots

The repository keeps only user-flow screenshots used in the video demo flow:
- [`docs/assets/screenshots/user-flow/`](docs/assets/screenshots/user-flow/)

## Support

For project questions, contact the team at:
- d.khasanshin@innopolis.university
- r.nasibullin@innopolis.university
- ro.ivanov@innopolis.university
- n.selezenev@innopolis.university
- ars.laptev@innopolis.university

## Issues

Use the **Issues** tab of the current repository.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
