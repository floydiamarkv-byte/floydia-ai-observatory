"""
Tests unitarios para la seguridad del servidor web (V-02, V-03, V-09, V-17, V-23).
"""

import unittest
import socket
import threading
import time
import urllib.request
import urllib.error
import json
from src.web.app import FloydIAWebServer, AUTH_TOKEN, start_server
import socketserver


class TestWebServerSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_port = 8399
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        cls.server = socketserver.ThreadingTCPServer(("127.0.0.1", cls.test_port), FloydIAWebServer)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_post_action_forbidden_without_token(self):
        url = f"http://127.0.0.1:{self.test_port}/api/action/probe"
        req = urllib.request.Request(url, method="POST", data=b"{}")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 403)

    def test_get_unauthorized_static_path_returns_404(self):
        # Asegura que /.env o rutas del árbol no se sirvan (Fix V-03)
        url = f"http://127.0.0.1:{self.test_port}/.env"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url)
        self.assertEqual(ctx.exception.code, 404)

    def test_get_rankings_api_success(self):
        url = f"http://127.0.0.1:{self.test_port}/api/rankings"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
