# Suggested Team Split (5 Students)

## Student 1: Networking and Protocol

- `network.py`
- framing and RPC behavior
- protocol consistency checks in `protocol.md`

## Student 2: DHT-like Lookup and Membership

- `dht.py`
- `membership.py`
- join/leave and routing behavior in `peer.py`

## Student 3: Storage and Metadata

- `storage.py`
- `metadata.py`
- manifest/chunk integrity handling

## Student 4: Download Orchestration and CLI Demo UX

- `downloader.py`
- CLI command flow in `cli.py`
- progress and runtime observability

## Student 5: Integration, Tests, and Documentation

- `tests/`
- `README.md`
- `docs/report.md`, `docs/architecture.md`, `docs/demo.md`

## Integration rhythm

- Agree protocol payloads first
- Run integration test after each merged feature
- Keep demo scenario stable from the middle of the implementation phase
