from __future__ import annotations

from threading import Lock

from .protocol import PeerInfo


class MembershipView:
    def __init__(self, self_peer: PeerInfo) -> None:
        self.self_peer = self_peer
        self._peers: dict[str, PeerInfo] = {}
        self._lock = Lock()

    def add_peer(self, peer: PeerInfo) -> bool:
        if peer.peer_id == self.self_peer.peer_id:
            return False
        with self._lock:
            current = self._peers.get(peer.peer_id)
            changed = current != peer
            self._peers[peer.peer_id] = peer
            return changed

    def remove_peer(self, peer_id: str) -> bool:
        with self._lock:
            if peer_id in self._peers:
                self._peers.pop(peer_id)
                return True
            return False

    def merge_peers(self, peers: list[PeerInfo]) -> list[PeerInfo]:
        added: list[PeerInfo] = []
        for peer in peers:
            if self.add_peer(peer):
                added.append(peer)
        return added

    def get_peer(self, peer_id: str) -> PeerInfo | None:
        if peer_id == self.self_peer.peer_id:
            return self.self_peer
        with self._lock:
            return self._peers.get(peer_id)

    def all_peers(self, include_self: bool = True) -> list[PeerInfo]:
        with self._lock:
            peers = list(self._peers.values())
        if include_self:
            peers.append(self.self_peer)
        return peers

    def known_peers(self) -> list[PeerInfo]:
        with self._lock:
            return list(self._peers.values())

    def snapshot(self, include_self: bool = True) -> list[dict[str, str | int]]:
        return [peer.to_dict() for peer in self.all_peers(include_self=include_self)]
