# Final Report

## 1. Project overview

This project implements a simplified BitTorrent-style peer-to-peer file sharing system with DHT-like lookup for metadata placement and discovery.

The target was an educational system that is fully runnable and easy to explain during demonstration and oral defense.

## 2. Goals

Primary goals:
- Support file upload and full download using chunk exchange
- Use distributed metadata lookup (not a centralized tracker)
- Log key distributed events clearly
- Show per-peer download progress in terminal

Secondary goals:
- Keep code modular enough for a team of five
- Keep protocol and architecture simple for classroom explanation

## 3. Functional requirements addressed

Implemented requirements:
- Peer startup with local server
- Peer join through bootstrap node
- Membership view synchronization
- File chunking and manifest generation
- Distributed metadata registration for files and chunks
- DHT-like lookup routing for file/chunk metadata
- Chunk request/response transfer between peers
- File reconstruction and integrity checks
- Ownership updates after chunk reception
- Leave events and membership updates
- Download progress visualization per peer

## 4. Design decisions

Key decisions:
- Python 3.11 with standard library and `rich`
- TCP + JSON + explicit length framing
- Ring-based hash ownership with successor forwarding
- In-memory distributed metadata on responsible nodes
- CLI-first interface for reliable local demos

Rationale:
- Reduced implementation risk
- Clear mapping from protocol events to demo output
- Easy debugging and inspection during presentation

## 5. DHT-like lookup explanation

Each peer computes `peer_id = SHA1(host:port)`. File and chunk keys are hashed the same way. Peers are placed on a conceptual ring by peer ID.

The responsible peer for a key is the first clockwise peer with ID greater than or equal to the key hash. If a node handling a request is not responsible, it forwards the request to its successor. Forwarding continues until responsible node is reached.

This provides distributed ownership and routing behavior while remaining much simpler than full DHT protocols.

## 6. Implementation details

Core implementation areas:
- networking/protocol framing (`network.py`, `protocol.py`)
- lookup and ring logic (`dht.py`, `membership.py`)
- chunk storage and integrity (`storage.py`)
- metadata ownership tracking (`metadata.py`)
- orchestration and CLI (`peer.py`, `downloader.py`, `cli.py`)

Download flow integrity checks:
- each chunk SHA-256 verified on receive
- reconstructed file SHA-256 verified against manifest

## 7. Testing approach

Included tests:
- deterministic hashing and peer IDs
- ring sorting and routing behavior
- metadata registration/lookup
- file split and reconstruction
- integration test: 3 peers, upload on one peer, full download on another

The integration test validates the full end-to-end path required by the assignment.

## 8. Demo scenario

Recommended live scenario:
- start 3 peers
- upload file on peer A
- download file by file ID on peer C
- show logs for join, lookup routing, chunk ownership updates, chunk transfers
- show progress output and reconstructed file

Detailed command sequence is in `docs/demo.md`.

## 9. Limitations

Intentional simplifications:
- metadata not replicated across multiple responsible nodes
- no node-failure recovery for metadata loss
- no advanced scheduling, choking/unchoking, or tit-for-tat strategy
- no encryption or NAT traversal

These limits were chosen to keep project scope aligned with course expectations.

## 10. Future improvements

Possible extensions:
- lightweight replication of metadata to successor peers
- chunk rarity-based scheduling
- retry/backoff policy for failed owners
- optional persistent metadata snapshots
- transfer rate metrics and richer CLI dashboard

## 11. Conclusion

The project achieves the required functionality with a practical and explainable architecture. It demonstrates DHT-like distributed lookup, chunk-based file transfer, and end-to-end reconstruction while keeping complexity controlled for academic presentation.
