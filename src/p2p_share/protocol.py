from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import uuid


MESSAGE_JOIN = "join"
MESSAGE_JOIN_ACK = "join_ack"
MESSAGE_PEER_ANNOUNCE = "peer_announce"
MESSAGE_LEAVE = "leave"
MESSAGE_PING = "ping"
MESSAGE_STATE_SYNC = "state_sync"
MESSAGE_REGISTER_FILE = "register_file"
MESSAGE_LOOKUP_FILE = "lookup_file"
MESSAGE_REGISTER_CHUNK_OWNER = "register_chunk_owner"
MESSAGE_LOOKUP_CHUNK = "lookup_chunk"
MESSAGE_CHUNK_OWNERS = "chunk_owners"
MESSAGE_REQUEST_CHUNK = "request_chunk"
MESSAGE_SEND_CHUNK = "send_chunk"
MESSAGE_DOWNLOAD_STATUS = "download_status"
MESSAGE_ERROR = "error"


@dataclass(frozen=True)
class PeerInfo:
    host: str
    port: int
    peer_id: str

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        return {"host": self.host, "port": self.port, "peer_id": self.peer_id}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PeerInfo":
        return cls(host=str(value["host"]), port=int(value["port"]), peer_id=str(value["peer_id"]))


@dataclass(frozen=True)
class ChunkInfo:
    index: int
    chunk_id: str
    size: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "chunk_id": self.chunk_id,
            "size": self.size,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ChunkInfo":
        return cls(
            index=int(value["index"]),
            chunk_id=str(value["chunk_id"]),
            size=int(value["size"]),
            sha256=str(value["sha256"]),
        )


@dataclass(frozen=True)
class FileManifest:
    file_id: str
    file_name: str
    file_size: int
    file_sha256: str
    chunk_size: int
    chunks: list[ChunkInfo]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_sha256": self.file_sha256,
            "chunk_size": self.chunk_size,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "FileManifest":
        chunks = [ChunkInfo.from_dict(item) for item in value["chunks"]]
        return cls(
            file_id=str(value["file_id"]),
            file_name=str(value["file_name"]),
            file_size=int(value["file_size"]),
            file_sha256=str(value["file_sha256"]),
            chunk_size=int(value["chunk_size"]),
            chunks=chunks,
        )


def new_request_id() -> str:
    return uuid.uuid4().hex


def make_message(message_type: str, **payload: Any) -> dict[str, Any]:
    message = {"type": message_type, "request_id": new_request_id()}
    message.update(payload)
    return message
