import argparse
import asyncio
import sys
import traceback
 
from python_socks import ProxyConnectionError, ProxyError, ProxyTimeoutError
from python_socks.async_.asyncio.v2 import Proxy
 
VERBOSE = False
 
def debug(msg):
    if VERBOSE:
        print(f"[!] {msg}", flush=True)
def err(msg, tracebk=False):
    print(f"[!] {msg}", file=sys.stderr)
    if tracebk:
        traceback.print_exc()
def exp(exc, args):
    if isinstance(exc, (ProxyConnectionError, ConnectionRefusedError)):
        return f"[!] {args.onion}:{args.onion_port} is not reachable. is tor running? \n (systemctl status tor)"
    if isinstance(exc, (ProxyTimeoutError, asyncio.TimeoutError)):
        return f"[!] Timeout: {args.onion} is offline, slow or non-existent.\n"
    if isinstance(exc, ProxyError):
        return "[!] Tor refused the request: check if the .onion address and destination port are correct"
async def tunnel(reader, writer, label):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except asyncio.CancelledError:
        raise
    except (ConnectionError, OSError) as exc:
        debug(f"pipe {label} interrupted: {type(exc).__name__}: {exc}")
    finally:
        try:
            writer.close()
        except Exception:
            pass
async def hClient(client_r, client_w, args):
    peer = client_w.get_extra_info("peername")
    try:
        proxy = Proxy.from_url(f"socks5://{args.tor_host}:{args.tor_port}", rdns=True)
        sock = await asyncio.wait_for(
            proxy.connect(dest_host=args.onion, dest_port=args.onion_port),
            timeout=args.timeout,
        )
        onion_r, onion_w = await asyncio.open_connection(sock=sock)
    except Exception as exc:
        err(f"connection to {args.onion}:{args.onion_port} failed for {peer} -> "
            f"{type(exc).__name__}: {exc}\n{exp(exc, args) or ''}", tracebk=VERBOSE)
        client_w.close()
        return
    print(f"[+] {peer} -> {args.onion}:{args.onion_port}", flush=True)
    await asyncio.gather(
        tunnel(client_r, onion_w, "client->onion"),
        tunnel(onion_r, client_w, "onion->client"),
    )
async def main():
    global VERBOSE
    p = argparse.ArgumentParser(description="Local port -> .onion hidden service port via Tor")
    p.add_argument("--onion", required=True, help=".onion destination address")
    p.add_argument("--onion-port", type=int, required=True, help="destination port on the onion (required)")
    p.add_argument("--listen-host", default="127.0.0.1", help="listen interface (default: local only)")
    p.add_argument("--port", type=int, default=8080, help="local listening port (default: 8080)")
    p.add_argument("--tor-host", default="127.0.0.1")
    p.add_argument("--tor-port", type=int, default=9050)
    p.add_argument("--timeout", type=float, default=60.0, help="Tor connection timeout (s)")
    p.add_argument("-v", "--verbose", action="store_true", help="debug messages and tracebacks")
    args = p.parse_args()
    VERBOSE = args.verbose
    try:
        server = await asyncio.start_server(
            lambda r, w: hClient(r, w, args), args.listen_host, args.port
        )
    except OSError as exc:
        err(f"cannot listen on {args.listen_host}:{args.port}: {exc}", tracebk=VERBOSE)
        sys.exit(1)
    print(f"[*] listening on {args.listen_host}:{args.port} -> {args.onion}:{args.onion_port}", flush=True)
    async with server:
        await server.serve_forever()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)

