import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.server import Handler


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_health_and_ui(self):
        with urlopen(self.base + "/health") as response:
            self.assertEqual(json.load(response)["mode"], "demo")
        with urlopen(self.base + "/") as response:
            self.assertIn(b"CASE AGENT", response.read())
        with urlopen(self.base + "/app.js") as response:
            self.assertIn(b"analyze", response.read())

    def test_analyze_api(self):
        payload = json.dumps({"case": "O áudio não abre no celular do cliente."}).encode()
        req = Request(self.base + "/api/analyze", data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req) as response:
            result = json.load(response)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["mode"], "demo-deterministico")

    def test_rejects_wrong_media_type_and_large_input(self):
        req = Request(self.base + "/api/analyze", data=b"{}", headers={"Content-Type": "text/plain"})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 415)
        req = Request(self.base + "/api/analyze", data=b"x" * 16001, headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 413)


if __name__ == "__main__":
    unittest.main()
