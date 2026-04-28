from __future__ import annotations

import hashlib
from typing import Iterable

from .protocol import PeerInfo


def hash_text(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(digest, 16)


def make_peer_id(host: str, port: int) -> str:
    return hashlib.sha1(f"{host}:{port}".encode("utf-8")).hexdigest()


def short_id(peer_id: str, width: int = 8) -> str:
    return peer_id[:width]


def sort_ring(peers: Iterable[PeerInfo]) -> list[PeerInfo]:
    return sorted(peers, key=lambda peer: int(peer.peer_id, 16))


def responsible_peer_for_key(key: str, peers: Iterable[PeerInfo]) -> PeerInfo:
    ring = sort_ring(peers)
    if not ring:
        raise ValueError("Cannot compute owner in an empty ring")
    key_hash = hash_text(key)
    for peer in ring:
        if int(peer.peer_id, 16) >= key_hash:
            return peer
    return ring[0]


def successor_of(peer_id: str, peers: Iterable[PeerInfo]) -> PeerInfo:
    ring = sort_ring(peers)
    if not ring:
        raise ValueError("Cannot compute successor in an empty ring")
    positions = {peer.peer_id: idx for idx, peer in enumerate(ring)}
    if peer_id not in positions:
        return ring[0]
    next_index = (positions[peer_id] + 1) % len(ring)
    return ring[next_index]


def next_hop_for_key(
    current_peer_id: str,
    key: str,
    peers: Iterable[PeerInfo],
    visited: set[str] | None = None,
) -> PeerInfo:
    ring = sort_ring(peers)
    if not ring:
        raise ValueError("Cannot compute hop in an empty ring")

    visited = visited or set()
    responsible = responsible_peer_for_key(key, ring)
    if responsible.peer_id == current_peer_id:
        return responsible

    next_peer = successor_of(current_peer_id, ring)
    if next_peer.peer_id not in visited:
        return next_peer

    for peer in ring:
        if peer.peer_id not in visited:
            return peer

    return responsible
