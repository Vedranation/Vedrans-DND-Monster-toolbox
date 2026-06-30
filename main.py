"""Entry point: start the D&D Monster Toolbox web server.

Launches the Flask app from `server.app`. Equivalent to `python -m server.app`,
but provides a stable root entry point (`python main.py`) for the LAN/desktop run
and the future Android wrapper. Host/port/debug can be overridden via env vars
(DND_HOST / DND_PORT / DND_DEBUG) — the Android build will set DND_DEBUG=0.
"""

from __future__ import annotations

import os

from server.app import create_app


def main() -> None:
    app = create_app()
    host = os.environ.get("DND_HOST", "0.0.0.0")
    port = int(os.environ.get("DND_PORT", "8000"))
    debug = os.environ.get("DND_DEBUG", "1") != "0"
    # threaded=True so concurrent asset/API requests from the WebView don't block;
    # reloader stays off when debug is off (required when embedded in Android).
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=debug)


if __name__ == "__main__":
    main()
