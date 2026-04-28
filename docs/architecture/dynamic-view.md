# Dynamic View

## Join flow

1. New peer sends `join` to bootstrap peer.
2. Bootstrap responds with known peers.
3. New peer broadcasts `peer_announce` and `state_sync`.
4. Existing peers update membership and log join events.

## Upload flow

1. User executes `upload <path>`.
2. Peer splits file into chunks and stores chunks locally.
3. Peer sends `register_file` to responsible metadata node.
4. Peer sends `register_chunk_owner` for each chunk.
5. Responsible nodes persist metadata and log ownership updates.

## Download flow

1. User executes `download <file_id> [destination]`.
2. Downloader resolves manifest with `lookup_file`.
3. Downloader resolves owners for each chunk via `lookup_chunk`.
4. Downloader requests chunks from selected owners.
5. Downloader verifies hashes and stores chunks.
6. Downloader registers itself as a new chunk owner.
7. Downloader reconstructs final file and logs completion.
