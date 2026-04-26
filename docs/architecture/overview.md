# Architecture Overview

## Design goals

The project keeps the architecture simple, modular, and easy to explain during a course presentation.

Priority order:
1. End-to-end upload and download correctness
2. Understandable DHT-like lookup and membership behavior
3. Observable runtime logs and progress in CLI

## Package layout

- `src/p2p_share/domain`
  - core models and deterministic logic
  - hashing, ring ownership, metadata index, chunk storage, protocol schemas
- `src/p2p_share/application`
  - orchestration of peer lifecycle and download flow
  - request routing and high-level use cases
- `src/p2p_share/infrastructure`
  - TCP transport and logging adapters
- `src/p2p_share/interfaces`
  - CLI entrypoint and terminal presentation

## DHT-like lookup model

- `peer_id = SHA1(host:port)`
- file/chunk key hashes are mapped on the same ring
- responsible node is selected clockwise (first `peer_id >= key_hash`)
- non-responsible peers forward requests to ring successor
- forwarding uses `ttl` and `visited` to avoid loops

This is intentionally simpler than production DHT protocols and fits local demo constraints.

## Metadata model

- `register_file` stores manifests on the responsible peer for `file_id`
- `register_chunk_owner` stores owner records on the responsible peer for `chunk_id`
- `lookup_file` and `lookup_chunk` route through the ring

## Main flows

Upload flow:
1. Split file into chunks and compute hashes
2. Persist chunks locally
3. Register manifest in DHT-like metadata layer
4. Register owner entries for all local chunks

Download flow:
1. Resolve manifest by `file_id`
2. Resolve owners for each chunk
3. Request missing chunks from owners
4. Verify chunk hashes
5. Register self as new chunk owner
6. Reconstruct final file and verify full hash

## Tradeoffs

- metadata is in-memory on responsible peers
- no replication or failover logic
- no advanced piece scheduling
- no NAT traversal or encryption

These tradeoffs are deliberate for clarity and reliability in a student demo.
