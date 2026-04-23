from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from .config import DEFAULT_CHUNK_SIZE, DEFAULT_DATA_ROOT, DEFAULT_ROUTE_TTL
from .dht import make_peer_id, next_hop_for_key, responsible_peer_for_key, short_id
from .downloader import DownloadManager
from .logging_utils import EventLogger
from .membership import MembershipView
from .metadata import MetadataIndex
from .network import PeerServer, rpc_call
from .protocol import (
    MESSAGE_CHUNK_OWNERS,
    MESSAGE_DOWNLOAD_STATUS,
    MESSAGE_JOIN,
    MESSAGE_JOIN_ACK,
    MESSAGE_LEAVE,
    MESSAGE_LOOKUP_CHUNK,
    MESSAGE_LOOKUP_FILE,
    MESSAGE_PEER_ANNOUNCE,
    MESSAGE_PING,
    MESSAGE_REGISTER_CHUNK_OWNER,
    MESSAGE_REGISTER_FILE,
    MESSAGE_REQUEST_CHUNK,
    MESSAGE_SEND_CHUNK,
    MESSAGE_STATE_SYNC,
    FileManifest,
    PeerInfo,
    make_message,
)
from .storage import LocalStorage


class PeerNode:
    def __init__(
        self,
        host: str,
        port: int,
        data_root: Path | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        logger: EventLogger | None = None,
    ) -> None:
        peer_id = make_peer_id(host, port)
        self.self_info = PeerInfo(host=host, port=port, peer_id=peer_id)
        self.peer_id = peer_id
        self.chunk_size = chunk_size
        self.logger = logger or EventLogger()

        root = data_root if data_root is not None else Path(DEFAULT_DATA_ROOT)
        self.storage = LocalStorage(root / f"peer_{port}")
        self.membership = MembershipView(self.self_info)
        self.metadata = MetadataIndex()
        self.downloader = DownloadManager(self)

        self._server = PeerServer(host, port, self._handle_message)
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._server.start()
        self._running = True
        self.logger.info("peer_started", peer=self.self_info.address, peer_id=short_id(self.peer_id))
        self._rebroadcast_local_state()

    def stop(self, announce_leave: bool = True) -> None:
        if not self._running:
            return
        if announce_leave:
            self._broadcast(make_message(MESSAGE_LEAVE, peer=self.self_info.to_dict()))
            self.logger.info("peer_left", peer=self.self_info.address, peer_id=short_id(self.peer_id))
        self._server.stop()
        self._running = False
        self.logger.info("peer_stopped", peer=self.self_info.address)

    def join_network(self, host: str, port: int) -> None:
        bootstrap = PeerInfo(host=host, port=port, peer_id=make_peer_id(host, port))
        response = rpc_call(bootstrap, make_message(MESSAGE_JOIN, peer=self.self_info.to_dict()))
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error", "Join failed"))

        peers = [PeerInfo.from_dict(item) for item in response.get("peers", [])]
        self.membership.merge_peers(peers)

        announce = make_message(MESSAGE_PEER_ANNOUNCE, peer=self.self_info.to_dict())
        self._broadcast(announce)
        sync = make_message(MESSAGE_STATE_SYNC, peers=self.membership.snapshot(include_self=True))
        self._broadcast(sync)
        self._rebroadcast_local_state()
        self.logger.info("peer_joined_network", peer=self.self_info.address, via=f"{host}:{port}")

    def upload_file(self, file_path: Path) -> FileManifest:
        manifest, chunks = self.storage.split_file(file_path=file_path, chunk_size=self.chunk_size)
        for chunk_id, data in chunks.items():
            self.storage.save_chunk(chunk_id, data)
        self.storage.save_manifest(manifest)

        self.register_file_manifest(manifest.to_dict())
        for chunk in manifest.chunks:
            self.register_chunk_owner(chunk.chunk_id, self.self_info.to_dict())

        self.logger.info(
            "file_uploaded",
            peer=self.self_info.address,
            file_id=manifest.file_id,
            chunks=len(manifest.chunks),
            file=file_path.name,
        )
        return manifest

    def download_file(self, file_id: str, destination: Path) -> Path:
        return self.downloader.download(file_id=file_id, destination=destination)

    def register_file_manifest(self, manifest: dict[str, Any]) -> None:
        message = make_message(
            MESSAGE_REGISTER_FILE,
            manifest=manifest,
            ttl=DEFAULT_ROUTE_TTL,
            visited=[],
        )
        response = self._handle_message(message)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error", "register_file failed"))

    def register_chunk_owner(self, chunk_id: str, owner: dict[str, Any]) -> None:
        message = make_message(
            MESSAGE_REGISTER_CHUNK_OWNER,
            chunk_id=chunk_id,
            owner=owner,
            ttl=DEFAULT_ROUTE_TTL,
            visited=[],
        )
        response = self._handle_message(message)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error", "register_chunk_owner failed"))

    def lookup_file(self, file_id: str) -> dict[str, Any] | None:
        message = make_message(
            MESSAGE_LOOKUP_FILE,
            file_id=file_id,
            ttl=DEFAULT_ROUTE_TTL,
            visited=[],
        )
        response = self._handle_message(message)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error", "lookup_file failed"))
        return response.get("manifest")

    def lookup_chunk_owners(self, chunk_id: str) -> list[dict[str, Any]]:
        message = make_message(
            MESSAGE_LOOKUP_CHUNK,
            chunk_id=chunk_id,
            ttl=DEFAULT_ROUTE_TTL,
            visited=[],
        )
        response = self._handle_message(message)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error", "lookup_chunk failed"))
        return list(response.get("owners", []))

    def request_chunk(self, owner: dict[str, Any], chunk_id: str) -> bytes:
        owner_peer = PeerInfo.from_dict(owner)
        if owner_peer.peer_id == self.peer_id:
            return self.storage.load_chunk(chunk_id)

        response = rpc_call(owner_peer, make_message(MESSAGE_REQUEST_CHUNK, chunk_id=chunk_id))
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error", f"chunk request failed for {chunk_id}"))
        encoded = str(response["data"])
        return base64.b64decode(encoded.encode("utf-8"))

    def get_state(self) -> dict[str, Any]:
        return {
            "self": self.self_info.to_dict(),
            "known_peers": self.membership.snapshot(include_self=False),
            "local_manifests": self.storage.list_manifest_ids(),
            "metadata": self.metadata.snapshot(),
            "downloads": self.downloader.snapshot(),
        }

    def _local_manifests(self) -> list[FileManifest]:
        manifests: list[FileManifest] = []
        for file_id in self.storage.list_manifest_ids():
            try:
                manifests.append(self.storage.load_manifest(file_id))
            except Exception as exc:
                self.logger.warn("manifest_load_failed", file_id=file_id, error=str(exc))
        return manifests

    def _rebroadcast_local_state(self) -> None:
        owner = self.self_info.to_dict()
        for manifest in self._local_manifests():
            try:
                self.register_file_manifest(manifest.to_dict())
                for chunk in manifest.chunks:
                    if self.storage.has_chunk(chunk.chunk_id):
                        self.register_chunk_owner(chunk.chunk_id, owner)
            except Exception as exc:
                self.logger.warn("state_republish_failed", file_id=manifest.file_id, error=str(exc))

    def _handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        message_type = message.get("type")
        handlers: dict[str, Any] = {
            MESSAGE_JOIN: self._on_join,
            MESSAGE_PEER_ANNOUNCE: self._on_peer_announce,
            MESSAGE_LEAVE: self._on_leave,
            MESSAGE_PING: self._on_ping,
            MESSAGE_STATE_SYNC: self._on_state_sync,
            MESSAGE_REGISTER_FILE: self._on_register_file,
            MESSAGE_LOOKUP_FILE: self._on_lookup_file,
            MESSAGE_REGISTER_CHUNK_OWNER: self._on_register_chunk_owner,
            MESSAGE_LOOKUP_CHUNK: self._on_lookup_chunk,
            MESSAGE_REQUEST_CHUNK: self._on_request_chunk,
            MESSAGE_DOWNLOAD_STATUS: self._on_download_status,
        }
        handler = handlers.get(message_type)
        if handler is None:
            return {"status": "error", "error": f"Unsupported message type: {message_type}"}
        try:
            return handler(message)
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _on_join(self, message: dict[str, Any]) -> dict[str, Any]:
        peer = PeerInfo.from_dict(message["peer"])
        if self.membership.add_peer(peer):
            self.logger.info("peer_joined", peer=peer.address, peer_id=short_id(peer.peer_id))
            self._rebroadcast_local_state()
        return {"status": "ok", "type": MESSAGE_JOIN_ACK, "peers": self.membership.snapshot(include_self=True)}

    def _on_peer_announce(self, message: dict[str, Any]) -> dict[str, Any]:
        peer = PeerInfo.from_dict(message["peer"])
        if self.membership.add_peer(peer):
            self.logger.info("peer_joined", peer=peer.address, peer_id=short_id(peer.peer_id))
            self._rebroadcast_local_state()
        return {"status": "ok"}

    def _on_leave(self, message: dict[str, Any]) -> dict[str, Any]:
        peer = PeerInfo.from_dict(message["peer"])
        if self.membership.remove_peer(peer.peer_id):
            self.logger.info("peer_left", peer=peer.address, peer_id=short_id(peer.peer_id))
            self._rebroadcast_local_state()
        return {"status": "ok"}

    def _on_ping(self, _: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "type": "pong", "peer": self.self_info.to_dict()}

    def _on_state_sync(self, message: dict[str, Any]) -> dict[str, Any]:
        incoming = [PeerInfo.from_dict(item) for item in message.get("peers", [])]
        added = self.membership.merge_peers(incoming)
        for peer in added:
            self.logger.info("peer_discovered", peer=peer.address, peer_id=short_id(peer.peer_id))
        if added:
            self._rebroadcast_local_state()
        return {"status": "ok", "added": len(added)}

    def _on_register_file(self, message: dict[str, Any]) -> dict[str, Any]:
        manifest = dict(message["manifest"])
        file_id = str(manifest["file_id"])
        if self._is_responsible(file_id):
            self.metadata.register_file(manifest)
            self.logger.info(
                "file_registered",
                file_id=file_id,
                responsible=self.self_info.address,
            )
            return {"status": "ok", "type": MESSAGE_REGISTER_FILE}
        return self._forward_message(file_id, message)

    def _on_lookup_file(self, message: dict[str, Any]) -> dict[str, Any]:
        file_id = str(message["file_id"])
        if self._is_responsible(file_id):
            manifest = self.metadata.get_file(file_id)
            self.logger.info("lookup_file", file_id=file_id, responsible=self.self_info.address)
            return {"status": "ok", "type": MESSAGE_LOOKUP_FILE, "manifest": manifest}
        return self._forward_message(file_id, message)

    def _on_register_chunk_owner(self, message: dict[str, Any]) -> dict[str, Any]:
        chunk_id = str(message["chunk_id"])
        owner = dict(message["owner"])
        if self._is_responsible(chunk_id):
            self.metadata.register_chunk_owner(chunk_id, owner)
            self.logger.info(
                "chunk_owner_updated",
                chunk_id=chunk_id[:8],
                owner=f"{owner['host']}:{owner['port']}",
                responsible=self.self_info.address,
            )
            return {"status": "ok", "type": MESSAGE_REGISTER_CHUNK_OWNER}
        return self._forward_message(chunk_id, message)

    def _on_lookup_chunk(self, message: dict[str, Any]) -> dict[str, Any]:
        chunk_id = str(message["chunk_id"])
        if self._is_responsible(chunk_id):
            owners = self.metadata.get_chunk_owners(chunk_id)
            self.logger.info("lookup_chunk", chunk_id=chunk_id[:8], owners=len(owners))
            return {"status": "ok", "type": MESSAGE_CHUNK_OWNERS, "owners": owners}
        return self._forward_message(chunk_id, message)

    def _on_request_chunk(self, message: dict[str, Any]) -> dict[str, Any]:
        chunk_id = str(message["chunk_id"])
        if not self.storage.has_chunk(chunk_id):
            return {"status": "error", "error": f"Chunk not found: {chunk_id}"}
        data = self.storage.load_chunk(chunk_id)
        encoded = base64.b64encode(data).decode("utf-8")
        return {
            "status": "ok",
            "type": MESSAGE_SEND_CHUNK,
            "chunk_id": chunk_id,
            "size": len(data),
            "data": encoded,
        }

    def _on_download_status(self, _: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "downloads": self.downloader.snapshot()}

    def _is_responsible(self, key: str) -> bool:
        peers = self.membership.all_peers(include_self=True)
        responsible = responsible_peer_for_key(key, peers)
        return responsible.peer_id == self.peer_id

    def _forward_message(self, key: str, message: dict[str, Any]) -> dict[str, Any]:
        ttl = int(message.get("ttl", DEFAULT_ROUTE_TTL))
        visited = set(message.get("visited", []))
        visited.add(self.peer_id)

        if ttl <= 0:
            return {"status": "error", "error": f"Routing TTL exhausted for key {key}"}

        peers = self.membership.all_peers(include_self=True)
        next_hop = next_hop_for_key(self.peer_id, key, peers, visited=visited)
        if next_hop.peer_id == self.peer_id:
            return {"status": "error", "error": f"Cannot forward key {key}"}

        forwarded = dict(message)
        forwarded["ttl"] = ttl - 1
        forwarded["visited"] = list(visited)

        self.logger.info(
            "lookup_routed",
            key=key[:8],
            from_peer=self.self_info.address,
            to_peer=next_hop.address,
            ttl=ttl,
        )

        try:
            return rpc_call(next_hop, forwarded)
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _broadcast(self, message: dict[str, Any]) -> None:
        for peer in self.membership.known_peers():
            try:
                rpc_call(peer, message)
            except Exception:
                self.logger.warn("peer_unreachable", peer=peer.address)
