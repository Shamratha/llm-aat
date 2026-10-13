from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .financial_ner.pipeline import train_detector


class NERHandler(BaseHTTPRequestHandler):
    detector = None

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API name
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API name
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "privacy-preserving-financial-ner", "model": "hybrid"})
            return
        if self.path == "/demo":
            text = "Maya Rao emailed maya.rao@example.com about transaction TXN-48291."
            self._send(200, self.detector.redact(text))
            return
        self._send(404, {"error": "not_found", "message": "Use /health, /demo or POST /redact."})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API name
        if self.path != "/redact":
            self._send(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            text = body.get("text")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("text must be a non-empty string")
            method = body.get("method", "hybrid")
            if method not in {"hybrid", "rules", "model"}:
                raise ValueError("method must be hybrid, rules or model")
            self._send(200, self.detector.redact(text, method))
        except (ValueError, json.JSONDecodeError) as error:
            self._send(400, {"error": "invalid_request", "message": str(error)})


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    # The API uses a smaller deterministic demo corpus so startup stays quick.
    # The report metrics are produced with the full 600-example protocol.
    NERHandler.detector = train_detector(size=240)
    server = ThreadingHTTPServer(("127.0.0.1", port), NERHandler)
    print(f"Financial NER API listening at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
