"""Flask app factory for the D&D toolbox web server (Phase 1: JSON API only).

Wraps the pure engine/persistence layers. No Tkinter. WebSocket live-sync and
the static web UI arrive in later migration phases.

Run locally:
    python -m server.app            # serves on 0.0.0.0:8000

Binding to 0.0.0.0 makes it reachable on the PC's LAN IP (tablets) and on
localhost — and works unchanged inside an Android WebView wrapper later.
"""

from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def create_app() -> Flask:
    app = Flask(__name__)

    from server.api.attack import bp as attack_bp
    from server.api.board import bp as board_bp
    from server.api.core import bp as core_bp
    from server.api.monsters import bp as monsters_bp
    from server.api.players import bp as players_bp
    from server.api.initiative import bp as initiative_bp
    from server.api.presets import bp as presets_bp
    from server.api.rolls import bp as rolls_bp
    from server.api.search import bp as search_bp
    from server.api.settings import bp as settings_bp
    from server.api.spells import bp as spells_bp

    for bp in (core_bp, monsters_bp, players_bp, attack_bp, settings_bp, presets_bp,
               board_bp, rolls_bp, search_bp, initiative_bp, spells_bp):
        app.register_blueprint(bp)

    @app.errorhandler(HTTPException)
    def _json_errors(exc: HTTPException):
        return jsonify({"error": exc.name, "message": exc.description}), exc.code

    @app.get("/")
    def index():
        # Serves the web app shell (server/static/index.html).
        return app.send_static_file("index.html")

    @app.get("/favicon.ico")
    def favicon():
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=True)
