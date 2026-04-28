# Limitations

1. Metadata is stored in-memory on responsible peers, so metadata can be lost when those peers leave.
2. No replication of manifests or chunk-owner records is implemented.
3. Routing uses simple successor forwarding and does not optimize path length.
4. Chunk scheduling is basic and does not account for rarity or bandwidth.
5. Transfers are not encrypted and assume trusted local-network demo conditions.
6. Membership is eventually synchronized through announcements and state snapshots, not a strongly consistent protocol.

These are deliberate tradeoffs to keep the system understandable, stable in class demos, and aligned with course scope.
