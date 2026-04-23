from pathlib import Path

from p2p_share.storage import LocalStorage


def test_split_and_reconstruct(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"0123456789" * 1000)

    storage = LocalStorage(tmp_path / "peer")
    manifest, chunks = storage.split_file(source, chunk_size=256)

    for chunk_id, data in chunks.items():
        storage.save_chunk(chunk_id, data)

    storage.save_manifest(manifest)
    restored = storage.reconstruct_file(manifest, tmp_path / "restored.bin")

    assert restored.read_bytes() == source.read_bytes()
