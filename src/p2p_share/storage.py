from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .dht import hash_text
from .protocol import ChunkInfo, FileManifest


class StorageError(Exception):
    pass


class LocalStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.chunks_dir = base_dir / "chunks"
        self.manifests_dir = base_dir / "manifests"
        self.downloads_dir = base_dir / "downloads"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def split_file(self, file_path: Path, chunk_size: int) -> tuple[FileManifest, dict[str, bytes]]:
        source = file_path.read_bytes()
        file_sha = hashlib.sha256(source).hexdigest()
        file_id = hashlib.sha1(source).hexdigest()

        chunks: list[ChunkInfo] = []
        payloads: dict[str, bytes] = {}

        for index in range(0, len(source), chunk_size):
            chunk_bytes = source[index : index + chunk_size]
            chunk_hash = hashlib.sha256(chunk_bytes).hexdigest()
            chunk_index = index // chunk_size
            chunk_id = f"{hash_text(f'{file_id}:{chunk_index}:{chunk_hash}'):040x}"
            payloads[chunk_id] = chunk_bytes
            chunks.append(
                ChunkInfo(
                    index=chunk_index,
                    chunk_id=chunk_id,
                    size=len(chunk_bytes),
                    sha256=chunk_hash,
                )
            )

        manifest = FileManifest(
            file_id=file_id,
            file_name=file_path.name,
            file_size=len(source),
            file_sha256=file_sha,
            chunk_size=chunk_size,
            chunks=chunks,
        )
        return manifest, payloads

    def save_chunk(self, chunk_id: str, data: bytes) -> Path:
        path = self.chunks_dir / chunk_id
        path.write_bytes(data)
        return path

    def has_chunk(self, chunk_id: str) -> bool:
        return (self.chunks_dir / chunk_id).exists()

    def load_chunk(self, chunk_id: str) -> bytes:
        path = self.chunks_dir / chunk_id
        if not path.exists():
            raise StorageError(f"Chunk {chunk_id} does not exist")
        return path.read_bytes()

    def save_manifest(self, manifest: FileManifest) -> Path:
        path = self.manifests_dir / f"{manifest.file_id}.json"
        path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
        return path

    def load_manifest(self, file_id: str) -> FileManifest:
        path = self.manifests_dir / f"{file_id}.json"
        if not path.exists():
            raise StorageError(f"Manifest {file_id} does not exist")
        data = json.loads(path.read_text(encoding="utf-8"))
        return FileManifest.from_dict(data)

    def list_manifest_ids(self) -> list[str]:
        ids: list[str] = []
        for item in self.manifests_dir.glob("*.json"):
            ids.append(item.stem)
        ids.sort()
        return ids

    def reconstruct_file(self, manifest: FileManifest, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        output = bytearray()
        for chunk in sorted(manifest.chunks, key=lambda value: value.index):
            data = self.load_chunk(chunk.chunk_id)
            digest = hashlib.sha256(data).hexdigest()
            if digest != chunk.sha256:
                raise StorageError(f"Chunk hash mismatch for {chunk.chunk_id}")
            output.extend(data)

        file_digest = hashlib.sha256(output).hexdigest()
        if file_digest != manifest.file_sha256:
            raise StorageError("Final file hash mismatch")

        destination.write_bytes(bytes(output))
        return destination
