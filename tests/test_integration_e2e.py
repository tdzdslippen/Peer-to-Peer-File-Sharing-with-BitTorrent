from pathlib import Path
import socket
import time

import pytest

from p2p_share.peer import PeerNode


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", 0))
        except PermissionError:
            pytest.skip("Local socket binding is not allowed in this environment")
        return int(sock.getsockname()[1])


def test_upload_and_download_end_to_end(tmp_path: Path) -> None:
    p1_port = free_port()
    p2_port = free_port()
    p3_port = free_port()

    p1 = PeerNode("127.0.0.1", p1_port, data_root=tmp_path)
    p2 = PeerNode("127.0.0.1", p2_port, data_root=tmp_path)
    p3 = PeerNode("127.0.0.1", p3_port, data_root=tmp_path)

    peers = [p1, p2, p3]
    for peer in peers:
        peer.start()

    try:
        p2.join_network("127.0.0.1", p1_port)
        p3.join_network("127.0.0.1", p1_port)
        time.sleep(0.4)

        source = tmp_path / "input.txt"
        source.write_text("distributed systems project integration test\n" * 200, encoding="utf-8")

        manifest = p1.upload_file(source)
        output = tmp_path / "output.txt"
        p3.download_file(manifest.file_id, output)

        assert output.read_bytes() == source.read_bytes()

        owners = p2.lookup_chunk_owners(manifest.chunks[0].chunk_id)
        owner_ids = {item["peer_id"] for item in owners}
        assert p3.peer_id in owner_ids
    finally:
        for peer in peers:
            peer.stop(announce_leave=True)
