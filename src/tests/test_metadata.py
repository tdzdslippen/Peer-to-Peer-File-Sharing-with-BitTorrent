from p2p_share.metadata import MetadataIndex


def test_register_and_lookup_file() -> None:
    metadata = MetadataIndex()
    manifest = {
        "file_id": "f1",
        "file_name": "a.txt",
        "file_size": 10,
        "file_sha256": "x",
        "chunk_size": 4,
        "chunks": [],
    }
    metadata.register_file(manifest)
    loaded = metadata.get_file("f1")
    assert loaded is not None
    assert loaded["file_name"] == "a.txt"


def test_register_chunk_owners() -> None:
    metadata = MetadataIndex()
    owner1 = {"host": "127.0.0.1", "port": 1, "peer_id": "p1"}
    owner2 = {"host": "127.0.0.1", "port": 2, "peer_id": "p2"}

    metadata.register_chunk_owner("c1", owner1)
    metadata.register_chunk_owner("c1", owner2)

    owners = metadata.get_chunk_owners("c1")
    ids = {item["peer_id"] for item in owners}
    assert ids == {"p1", "p2"}
