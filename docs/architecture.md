# Architecture

## Why this architecture

The implementation is intentionally simple and modular so that it is easy to explain in a course presentation and stable for a local demo. Each module maps to one clear responsibility.

This design prioritizes:
1. End-to-end correctness for upload/download with chunk exchange
2. Readable distributed logic for join, lookup, and ownership updates
3. Clear terminal demonstration with visible progress and events

## Module Responsibilities

- `peer.py`
  - Peer lifecycle
  - Message handling
  - Join/leave behavior
  - Routing requests through the DHT-like ring
- `network.py`
  - TCP server and client RPC
  - 4-byte length-prefixed framing for JSON messages
- `protocol.py`
  - Message type constants
  - `PeerInfo`, `ChunkInfo`, `FileManifest`
- `dht.py`
  - Peer ID hashing
  - Key hashing for files/chunks
  - Ring ordering and owner selection
  - Next-hop routing decision
- `membership.py`
  - Known peer table
  - Peer merge/remove operations
- `metadata.py`
  - Distributed storage of file manifests
  - Distributed storage of chunk ownership lists
- `storage.py`
  - File split to chunks
  - Local chunk persistence
  - Manifest persistence
  - File reconstruction with integrity checks
- `downloader.py`
  - Chunk download orchestration
  - Owner lookup and chunk requests
  - Per-peer progress display
- `cli.py`
  - Interactive peer shell
  - Command handling for demo flows

## DHT-like lookup strategy

Each peer has:
- `peer_id = SHA1(host:port)`

Each key has:
- `key_hash = SHA1(key)` for `file_id` or `chunk_id`

Peers are sorted by `peer_id` as a ring.

Owner selection:
- The responsible peer for a key is the first peer clockwise with `peer_id >= key_hash`
- If no such peer exists, ownership wraps to the smallest peer ID

Routing:
- If current peer is not responsible, it forwards to ring successor
- The request carries `ttl` and `visited` to avoid infinite loops
- Forwarding continues until the responsible peer handles the request

This is intentionally simpler than Chord/Kademlia but still demonstrates distributed key ownership and request routing.

## Metadata model

- `register_file` stores a file manifest on the responsible peer for `file_id`
- `register_chunk_owner` stores owner records on the responsible peer for `chunk_id`
- `lookup_file` and `lookup_chunk` route through the ring to the responsible node

Metadata is in-memory per responsible peer, which keeps the project simple for local demos.

## Upload data flow

1. User calls `upload <path>` on a peer
2. File is split into fixed-size chunks
3. Chunk hashes and chunk IDs are computed
4. Manifest is created and saved locally
5. Manifest is routed to responsible peer (`register_file`)
6. Each chunk owner record is routed (`register_chunk_owner`)
7. Events are logged: upload, registration, ownership updates

## Download data flow

1. User calls `download <file_id> <destination>`
2. Requester resolves manifest via `lookup_file`
3. For each chunk, requester resolves owners via `lookup_chunk`
4. Requester asks an owner with `request_chunk`
5. Requester verifies hash, stores chunk, and registers itself as owner
6. Progress is shown in terminal (`x/y chunks`)
7. After all chunks arrive, file is reconstructed and verified

## Join and leave handling

Join:
- New peer contacts bootstrap peer with `join`
- Bootstrap returns known peers (`join_ack`)
- New peer announces itself and syncs membership
- Join events are logged by receiving peers

Leave:
- Peer sends `leave` to known peers before shutdown
- Receivers remove the peer from membership
- Leave events are logged

## Tradeoffs and simplifications

- Metadata is memory-based, not persisted cluster-wide
- No replication or fault-tolerant rebalancing
- No advanced piece scheduling algorithm
- No NAT traversal, encryption, or production retry policy

These choices keep the implementation stable, understandable, and aligned with course-level scope.
