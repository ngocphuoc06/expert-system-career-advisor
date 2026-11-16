from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PORT = 8000


def main() -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(PROJECT_ROOT))
    with ThreadingHTTPServer(("", PORT), handler) as server:
        print(
            f"Serving HTTP on port {PORT} "
            f"(http://localhost:{PORT}/website/) ...",
            flush=True,
        )
        server.serve_forever()


if __name__ == "__main__":
    main()
