from pathlib import Path
import socket
import time
import hashlib

import pytest

from p2p_share.dht import responsible_peer_for_key
from p2p_share.peer import PeerNode


def free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except PermissionError:
        pytest.skip("Local socket binding is not allowed in this environment")


def find_source_for_new_owner(initial_peers: list, final_peers: list, target_peer_id: str) -> str:
    for attempt in range(1, 5000):
        source = f"late join metadata rebalance test {attempt}\n" * 8
        file_id = hashlib.sha1(source.encode("utf-8")).hexdigest()
        initial_owner = responsible_peer_for_key(file_id, initial_peers).peer_id
        final_owner = responsible_peer_for_key(file_id, final_peers).peer_id
        if initial_owner != final_owner and final_owner == target_peer_id:
            return source
    raise AssertionError("could not find a file_id that reassigns ownership to the new peer")


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


def test_late_join_republishes_metadata_for_new_responsible_peer(tmp_path: Path) -> None:
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
        time.sleep(0.4)

        source_text = find_source_for_new_owner(
            initial_peers=p1.membership.all_peers(include_self=True),
            final_peers=[p1.self_info, p2.self_info, p3.self_info],
            target_peer_id=p3.peer_id,
        )
        source = tmp_path / "late_join_input.txt"
        source.write_text(source_text, encoding="utf-8")

        manifest = p1.upload_file(source)

        p3.join_network("127.0.0.1", p1_port)

        deadline = time.time() + 2.0
        while time.time() < deadline:
            if p3.lookup_file(manifest.file_id) is not None:
                break
            time.sleep(0.1)
        else:
            pytest.fail("late-joining peer never received republished file metadata")

        output = tmp_path / "late_join_output.txt"
        p3.download_file(manifest.file_id, output)

        assert output.read_bytes() == source.read_bytes()
    finally:
        for peer in peers:
            peer.stop(announce_leave=True)
