# Demo Guide

## Demo objective

Show a complete 3-peer flow that validates:
- join and leave logging
- distributed metadata lookup
- chunk ownership updates
- complete upload/download by chunk exchange
- per-peer download progress

## Preparation

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

Create a sample file:

```bash
printf "DNP demo content\n%.0s" {1..400} > sample.txt
```

## Terminal layout

Open three terminals.

### Terminal 1 (Peer A)

```bash
p2p-peer --host 127.0.0.1 --port 9101
```

### Terminal 2 (Peer B)

```bash
p2p-peer --host 127.0.0.1 --port 9102 --bootstrap 127.0.0.1:9101
```

### Terminal 3 (Peer C)

```bash
p2p-peer --host 127.0.0.1 --port 9103 --bootstrap 127.0.0.1:9101
```

## Demo steps

1. On Peer A run:

```text
upload ./sample.txt
```

2. Copy printed `file_id`.

3. On Peer C run:

```text
download <file_id> ./downloaded_sample.txt
```

4. On Peer C run:

```text
progress
```

5. On any peer run:

```text
chunks <file_id>
```

6. On all peers run:

```text
peers
state
```

7. To demonstrate leave handling, exit Peer B:

```text
leave
```

## Expected logs and outputs

During join:
- `peer_joined`
- `peer_joined_network`
- `peer_discovered`

During upload:
- `file_uploaded`
- `file_registered`
- `chunk_owner_updated`

During download:
- `lookup_routed`
- `lookup_file`
- `lookup_chunk`
- `chunk_requested`
- `chunk_received`
- `download_completed`

During leave:
- `peer_left`
- `peer_stopped`

## Oral presentation talking points

- Why simplified ring-based DHT was chosen instead of full Kademlia/Chord
- How key ownership is assigned by consistent-hash-like logic
- How metadata and chunk owners are resolved without a central tracker
- How chunk ownership updates allow peers to become new chunk sources
- Which production concerns were intentionally excluded from this project

## Typical questions and concise answers

Q: Why is this called DHT-like and not full DHT?
A: It uses distributed hash ownership and routing but omits advanced routing tables, replication, and failure recovery.

Q: What happens when a responsible peer leaves?
A: In this version metadata may be lost because replication is not implemented.

Q: How do you verify correctness of downloaded files?
A: Every chunk hash is validated, then full file hash is validated during reconstruction.
