# Protocol

## Overview

Transport:
- TCP

Framing:
- 4-byte big-endian payload length
- UTF-8 JSON payload

RPC style:
- one request message per connection
- one response message per connection

Chunk payload transfer:
- `request_chunk` response includes Base64 encoded chunk bytes

## Common fields

Most requests include:
- `type`: message type
- `request_id`: generated client-side ID

Routing-enabled messages include:
- `ttl`: remaining forwarding budget
- `visited`: list of peer IDs already traversed

## Message Types

### `join`
Request:
```json
{
  "type": "join",
  "request_id": "...",
  "peer": {"host": "127.0.0.1", "port": 9102, "peer_id": "..."}
}
```

Response (`join_ack`):
```json
{
  "status": "ok",
  "type": "join_ack",
  "peers": [{"host": "127.0.0.1", "port": 9101, "peer_id": "..."}]
}
```

### `peer_announce`
Notify known peers about a newly joined peer.

### `leave`
Notify known peers that a peer is leaving.

### `state_sync`
Exchange current peer list snapshot.

### `ping`
Health check message.

### `register_file`
Register file manifest in DHT-like metadata storage.

Request:
```json
{
  "type": "register_file",
  "request_id": "...",
  "manifest": {
    "file_id": "...",
    "file_name": "sample.txt",
    "file_size": 1234,
    "file_sha256": "...",
    "chunk_size": 65536,
    "chunks": [
      {"index": 0, "chunk_id": "...", "size": 1234, "sha256": "..."}
    ]
  },
  "ttl": 12,
  "visited": []
}
```

### `lookup_file`
Resolve file manifest by `file_id` through ring routing.

### `register_chunk_owner`
Register owner of a chunk.

Request:
```json
{
  "type": "register_chunk_owner",
  "request_id": "...",
  "chunk_id": "...",
  "owner": {"host": "127.0.0.1", "port": 9101, "peer_id": "..."},
  "ttl": 12,
  "visited": []
}
```

### `lookup_chunk`
Resolve all known owners for a chunk.

Response (`chunk_owners`):
```json
{
  "status": "ok",
  "type": "chunk_owners",
  "owners": [
    {"host": "127.0.0.1", "port": 9101, "peer_id": "..."},
    {"host": "127.0.0.1", "port": 9103, "peer_id": "..."}
  ]
}
```

### `request_chunk`
Request chunk bytes from a peer that owns it.

Request:
```json
{
  "type": "request_chunk",
  "request_id": "...",
  "chunk_id": "..."
}
```

Response (`send_chunk`):
```json
{
  "status": "ok",
  "type": "send_chunk",
  "chunk_id": "...",
  "size": 4096,
  "data": "<base64>"
}
```

### `download_status`
Retrieve active/completed download status from a peer.

## Chunk transfer flow

1. Downloader calls `lookup_file(file_id)`
2. Downloader loops all chunks from manifest
3. For each chunk, downloader calls `lookup_chunk(chunk_id)`
4. Downloader selects an owner and sends `request_chunk`
5. Downloader verifies chunk hash and stores chunk
6. Downloader sends `register_chunk_owner` for itself
7. After all chunks, downloader reconstructs file and verifies final hash

## Error handling

Response error format:
```json
{
  "status": "error",
  "error": "human-readable reason"
}
```

Main error cases:
- unsupported message type
- chunk not found at requested peer
- routing TTL exhausted
- no owners found for a chunk
- hash mismatch during validation
