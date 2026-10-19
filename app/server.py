import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .providers import DemoProvider, OllamaProvider
from .workflow import Workbench

INDEX = Path(__file__).resolve().parents[1] / "web" / "index.html"
SCRIPT = Path(__file__).resolve().parents[1] / "web" / "app.js"
MODE = os.getenv("WORKBENCH_MODE", "demo").lower()
if MODE not in {"demo", "ollama"}:
    raise SystemExit("WORKBENCH_MODE deve ser demo ou ollama")
WORKBENCH = Workbench(provider=OllamaProvider() if MODE == "ollama" else DemoProvider())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Não registre o conteúdo dos casos ou respostas por acidente.
        if args and isinstance(args[0], str):
            super().log_message("%s", args[0].split("?")[0])

    def send_bytes(self, status: int, data: bytes, mime: str):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, status: int, body: dict):
        self.send_bytes(status, json.dumps(body, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path == "/":
            self.send_bytes(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/app.js":
            self.send_bytes(200, SCRIPT.read_bytes(), "text/javascript; charset=utf-8")
        elif self.path == "/health":
            self.json_response(200, {"status": "ok", "mode": MODE})
        else:
            self.json_response(404, {"error": "não encontrado"})

    def do_POST(self):
        if self.path != "/api/analyze":
            return self.json_response(404, {"error": "não encontrado"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self.json_response(415, {"error": "envie application/json"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16000:
                return self.json_response(413, {"error": "requisição vazia ou grande demais"})
            body = json.loads(self.rfile.read(length))
            result = WORKBENCH.analyze(body["case"])
            return self.json_response(200, result)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return self.json_response(400, {"error": str(exc)[:200]})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8086), Handler)
    print(f"Case Agent Workbench em http://127.0.0.1:8086 (modo {MODE})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
