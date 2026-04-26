from p2p_share.domain.dht import hash_text, make_peer_id


def test_peer_id_is_stable() -> None:
    left = make_peer_id("127.0.0.1", 9000)
    right = make_peer_id("127.0.0.1", 9000)
    assert left == right


def test_peer_id_changes_with_port() -> None:
    first = make_peer_id("127.0.0.1", 9000)
    second = make_peer_id("127.0.0.1", 9001)
    assert first != second


def test_hash_text_is_deterministic() -> None:
    assert hash_text("abc") == hash_text("abc")
    assert hash_text("abc") != hash_text("abcd")
