# Deployment View

## Local demo topology

- 3 to 5 peer processes on one machine or local network.
- Each process runs one TCP server bound to `host:port`.
- Each peer has its own runtime storage directory.

## Runtime artifacts

For each peer:
- local chunks directory
- local manifests directory
- reconstructed downloads directory
- in-memory membership and metadata maps

## Expected communication pattern

- short RPC-like TCP connections
- JSON control messages with 4-byte length framing
- Base64 payload only for chunk transfer responses

This deployment model is chosen for stable classroom demonstrations and easy reproducibility.
