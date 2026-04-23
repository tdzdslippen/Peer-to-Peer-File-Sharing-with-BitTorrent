from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any


class MetadataIndex:
    def __init__(self) -> None:
        self._files: dict[str, dict[str, Any]] = {}
        self._chunk_owners: dict[str, dict[str, dict[str, Any]]] = {}
        self._lock = Lock()

    def register_file(self, manifest: dict[str, Any]) -> None:
        file_id = str(manifest["file_id"])
        with self._lock:
            self._files[file_id] = deepcopy(manifest)

    def get_file(self, file_id: str) -> dict[str, Any] | None:
        with self._lock:
            manifest = self._files.get(file_id)
            return deepcopy(manifest) if manifest is not None else None

    def register_chunk_owner(self, chunk_id: str, owner: dict[str, Any]) -> None:
        owner_id = str(owner["peer_id"])
        with self._lock:
            owners = self._chunk_owners.setdefault(chunk_id, {})
            owners[owner_id] = deepcopy(owner)

    def get_chunk_owners(self, chunk_id: str) -> list[dict[str, Any]]:
        with self._lock:
            owners = self._chunk_owners.get(chunk_id, {})
            return [deepcopy(owner) for owner in owners.values()]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            files = deepcopy(self._files)
            chunk_owners = {chunk_id: list(owners.values()) for chunk_id, owners in self._chunk_owners.items()}
        return {"files": files, "chunk_owners": chunk_owners}
