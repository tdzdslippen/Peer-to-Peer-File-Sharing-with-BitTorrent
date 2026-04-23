from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex

from rich.console import Console
from rich.table import Table

from .config import DEFAULT_CHUNK_SIZE, DEFAULT_DATA_ROOT, DEFAULT_HOST
from .peer import PeerNode


def parse_address(address: str) -> tuple[str, int]:
    host, port_text = address.split(":", maxsplit=1)
    return host, int(port_text)


def render_peers(console: Console, peer: PeerNode) -> None:
    table = Table(title="Known Peers")
    table.add_column("Peer ID")
    table.add_column("Host")
    table.add_column("Port")
    table.add_column("Role")

    table.add_row(peer.peer_id[:8], peer.self_info.host, str(peer.self_info.port), "self")
    for info in sorted(peer.membership.known_peers(), key=lambda value: value.peer_id):
        table.add_row(info.peer_id[:8], info.host, str(info.port), "known")
    console.print(table)


def render_downloads(console: Console, peer: PeerNode) -> None:
    table = Table(title="Download Progress")
    table.add_column("File ID")
    table.add_column("Progress")
    table.add_column("Completed")
    for item in peer.downloader.snapshot():
        progress = f"{item['downloaded_chunks']}/{item['total_chunks']}"
        table.add_row(str(item["file_id"])[:12], progress, str(item["completed"]))
    if not peer.downloader.snapshot():
        table.add_row("-", "-", "-")
    console.print(table)


def render_chunk_owners(console: Console, peer: PeerNode, file_id: str) -> None:
    manifest = peer.lookup_file(file_id)
    if manifest is None:
        console.print(f"File {file_id} is not known in DHT metadata")
        return

    table = Table(title=f"Chunk Ownership for {file_id[:12]}")
    table.add_column("Chunk")
    table.add_column("Owners")
    chunks = manifest.get("chunks", [])
    for chunk in chunks:
        chunk_id = str(chunk["chunk_id"])
        owners = peer.lookup_chunk_owners(chunk_id)
        owner_text = ", ".join(f"{owner['host']}:{owner['port']}" for owner in owners) if owners else "none"
        table.add_row(chunk_id[:12], owner_text)
    console.print(table)


def run_shell(peer: PeerNode) -> None:
    console = Console()

    help_text = """
Commands:
  help
  join <host:port>
  upload <path>
  download <file_id> [destination]
  peers
  files
  lookup <file_id>
  chunks <file_id>
  progress
  state
  leave
  exit
""".strip()

    console.print(help_text)
    while True:
        try:
            raw = input(f"peer[{peer.self_info.port}]> ").strip()
        except EOFError:
            raw = "exit"
        except KeyboardInterrupt:
            raw = "exit"

        if not raw:
            continue

        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            console.print(f"Invalid command: {exc}")
            continue

        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "help":
                console.print(help_text)
            elif command == "join":
                host, port = parse_address(args[0])
                peer.join_network(host, port)
            elif command == "upload":
                path = Path(args[0]).expanduser().resolve()
                manifest = peer.upload_file(path)
                console.print(f"Uploaded file_id={manifest.file_id} chunks={len(manifest.chunks)}")
            elif command == "download":
                file_id = args[0]
                if len(args) > 1:
                    destination = Path(args[1]).expanduser().resolve()
                else:
                    destination = (peer.storage.downloads_dir / f"{file_id}.bin").resolve()
                output = peer.download_file(file_id, destination)
                console.print(f"Downloaded to {output}")
            elif command == "peers":
                render_peers(console, peer)
            elif command == "files":
                ids = peer.storage.list_manifest_ids()
                if not ids:
                    console.print("No local manifests")
                for file_id in ids:
                    console.print(file_id)
            elif command == "lookup":
                file_id = args[0]
                manifest = peer.lookup_file(file_id)
                console.print(json.dumps(manifest, indent=2) if manifest else "not found")
            elif command == "chunks":
                render_chunk_owners(console, peer, args[0])
            elif command == "progress":
                render_downloads(console, peer)
            elif command == "state":
                console.print_json(data=peer.get_state())
            elif command in {"leave", "exit", "quit"}:
                peer.stop(announce_leave=True)
                break
            else:
                console.print("Unknown command. Type 'help'.")
        except (IndexError, ValueError):
            console.print("Invalid command arguments")
        except Exception as exc:
            console.print(f"Command failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="P2P file sharing peer")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--data-root", default=DEFAULT_DATA_ROOT)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--bootstrap", default=None)
    args = parser.parse_args()

    peer = PeerNode(
        host=args.host,
        port=args.port,
        data_root=Path(args.data_root),
        chunk_size=args.chunk_size,
    )
    peer.start()
    if args.bootstrap is not None:
        host, port = parse_address(args.bootstrap)
        peer.join_network(host, port)

    try:
        run_shell(peer)
    finally:
        peer.stop(announce_leave=True)


if __name__ == "__main__":
    main()
