# Caronte

A lightweight TCP forwarder that relays local traffic to a Tor hidden service.

Caronte opens a single local port and forwards every incoming TCP connection to a `.onion` address through Tor's SOCKS5 proxy. It works at the transport layer: HTTP, HTTPS (TLS end-to-end), or any other protocol. No parsing, no termination, no inspection — bytes in, bytes out.

Originally written to move HTTP/HTTPS traffic to a hidden service without exposing the backend's real IP and without breaking TLS.

## How it works

```
Client  →  Caronte  →  SOCKS5 (Tor)  →  .onion service
```

Each incoming connection opens a matching SOCKS5 stream through Tor. Caronte then copies bytes in both directions until one side closes.

Because it operates at the transport layer, TLS remains end-to-end between the client and the onion service. Caronte never sees plaintext.

## Requirements

- Python 3.8+
- `python-socks[asyncio]`
- A running Tor daemon with `SocksPort` enabled (default `127.0.0.1:9050`)

```bash
pip install "python-socks[asyncio]"
```

## Usage

```bash
python caronte.py --onion <address>.onion --onion-port 443 --port 8080
```

Then point any client at `127.0.0.1:8080`:

```bash
curl http://127.0.0.1:8080/
curl -k https://127.0.0.1:8080/
```

## Options

| Flag | Default | Description |
|---|---|---|
| `--onion` | — | `.onion` destination address (required) |
| `--onion-port` | — | destination port on the onion service (required) |
| `--listen-host` | `127.0.0.1` | listen interface |
| `--port` | `8080` | local listening port |
| `--tor-host` | `127.0.0.1` | Tor SOCKS5 host |
| `--tor-port` | `9050` | Tor SOCKS5 port |
| `--timeout` | `60.0` | Tor connection timeout in seconds |
| `-v`, `--verbose` | off | debug messages and tracebacks |

## Notes

- Works at the transport layer, not as an HTTP proxy
- TLS stays end-to-end between client and onion service
- Output goes to stdout/stderr only

## License

MIT


