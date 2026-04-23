from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
from threading import Lock

from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from .dht import short_id
from .protocol import FileManifest


@dataclass
class DownloadStatus:
    file_id: str
    total_chunks: int
    downloaded_chunks: int
    completed: bool


class DownloadManager:
    def __init__(self, peer: "PeerNode") -> None:
        self.peer = peer
        self._lock = Lock()
        self._status: dict[str, DownloadStatus] = {}

    def snapshot(self) -> list[dict[str, str | int | bool]]:
        with self._lock:
            items = list(self._status.values())
        return [
            {
                "file_id": item.file_id,
                "total_chunks": item.total_chunks,
                "downloaded_chunks": item.downloaded_chunks,
                "completed": item.completed,
            }
            for item in items
        ]

    def download(self, file_id: str, destination: Path) -> Path:
        manifest_dict = self.peer.lookup_file(file_id)
        if manifest_dict is None:
            raise RuntimeError(f"File {file_id} not found")

        manifest = FileManifest.from_dict(manifest_dict)
        total = len(manifest.chunks)
        state = DownloadStatus(file_id=file_id, total_chunks=total, downloaded_chunks=0, completed=False)

        with self._lock:
            self._status[file_id] = state

        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} chunks"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            transient=True,
        )

        task_name = f"peer {short_id(self.peer.peer_id)} downloading {file_id[:8]}"

        with progress:
            task = progress.add_task(task_name, total=total)
            for chunk in sorted(manifest.chunks, key=lambda value: value.index):
                if self.peer.storage.has_chunk(chunk.chunk_id):
                    state.downloaded_chunks += 1
                    progress.advance(task)
                    continue

                owners = self.peer.lookup_chunk_owners(chunk.chunk_id)
                if not owners:
                    raise RuntimeError(f"No owners found for chunk {chunk.chunk_id}")

                data = self._download_chunk_from_owners(chunk.chunk_id, chunk.sha256, owners)
                self.peer.storage.save_chunk(chunk.chunk_id, data)
                self.peer.register_chunk_owner(chunk.chunk_id, self.peer.self_info.to_dict())
                state.downloaded_chunks += 1
                progress.advance(task)
                self.peer.logger.info(
                    "chunk_received",
                    peer=self.peer.self_info.address,
                    chunk_id=chunk.chunk_id[:8],
                    done=f"{state.downloaded_chunks}/{state.total_chunks}",
                )

        self.peer.storage.save_manifest(manifest)
        output_path = self.peer.storage.reconstruct_file(manifest, destination)
        state.completed = True
        self.peer.logger.info(
            "download_completed",
            peer=self.peer.self_info.address,
            file_id=file_id,
            output=str(output_path),
        )
        return output_path

    def _download_chunk_from_owners(self, chunk_id: str, expected_sha: str, owners: list[dict[str, str | int]]) -> bytes:
        last_error: Exception | None = None
        for owner in owners:
            try:
                data = self.peer.request_chunk(owner, chunk_id)
                digest = hashlib.sha256(data).hexdigest()
                if digest != expected_sha:
                    raise RuntimeError(f"Chunk hash mismatch from owner {owner['peer_id']}")
                self.peer.logger.info(
                    "chunk_requested",
                    requester=self.peer.self_info.address,
                    owner=f"{owner['host']}:{owner['port']}",
                    chunk_id=chunk_id[:8],
                )
                return data
            except Exception as exc:
                last_error = exc
        if last_error is None:
            raise RuntimeError(f"Chunk {chunk_id} download failed")
        raise RuntimeError(f"Chunk {chunk_id} download failed: {last_error}")
