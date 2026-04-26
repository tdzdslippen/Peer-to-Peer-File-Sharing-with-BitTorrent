# Static View

## Source code modules

- `domain/config.py`
- `domain/protocol.py`
- `domain/dht.py`
- `domain/membership.py`
- `domain/metadata.py`
- `domain/storage.py`
- `infrastructure/network.py`
- `infrastructure/logging_utils.py`
- `application/peer.py`
- `application/downloader.py`
- `interfaces/cli.py`

## Responsibility boundaries

- Domain layer contains deterministic logic and data contracts.
- Infrastructure layer contains external I/O adapters.
- Application layer composes domain + infrastructure for runtime behavior.
- Interface layer exposes CLI commands and output formatting.
