from p2p_share.dht import next_hop_for_key, responsible_peer_for_key, sort_ring
from p2p_share.protocol import PeerInfo


PEERS = [
    PeerInfo(host="127.0.0.1", port=9001, peer_id=f"{0x1000000000000000000000000000000000000000:040x}"),
    PeerInfo(host="127.0.0.1", port=9002, peer_id=f"{0x5000000000000000000000000000000000000000:040x}"),
    PeerInfo(host="127.0.0.1", port=9003, peer_id=f"{0x9000000000000000000000000000000000000000:040x}"),
]


def test_sort_ring_orders_by_peer_id() -> None:
    ring = sort_ring(reversed(PEERS))
    assert [peer.port for peer in ring] == [9001, 9002, 9003]


def test_responsible_peer_is_one_of_ring_nodes() -> None:
    owner = responsible_peer_for_key("file-key", PEERS)
    assert owner.port in {9001, 9002, 9003}


def test_next_hop_moves_clockwise() -> None:
    key = "key-for-clockwise-hop"
    while responsible_peer_for_key(key, PEERS).peer_id == PEERS[0].peer_id:
        key = f"{key}-x"
    hop = next_hop_for_key(current_peer_id=PEERS[0].peer_id, key=key, peers=PEERS, visited=set())
    assert hop.port == 9002


def test_next_hop_skips_visited_nodes() -> None:
    key = "key-for-skip-hop"
    while responsible_peer_for_key(key, PEERS).peer_id == PEERS[0].peer_id:
        key = f"{key}-x"
    hop = next_hop_for_key(
        current_peer_id=PEERS[0].peer_id,
        key=key,
        peers=PEERS,
        visited={PEERS[1].peer_id},
    )
    assert hop.port in {9001, 9003}
