import contextlib
import importlib
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from llm import client


def make_server(chunks, seen):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            seen["auth"] = self.headers.get("Authorization")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def do_POST(self):
            seen["auth"] = self.headers.get("Authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for d in chunks:
                self.wfile.write(b"data: " + json.dumps({"choices": [{"delta": d}]}).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_port


CHUNKS = [{"reasoning_content": "hmm"}, {"content": "Olá"}, {"content": " mundo"}]


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.seen = {}
        self.srv, self.url = make_server(CHUNKS, self.seen)
        self.addCleanup(self.srv.shutdown)

    def test_stream_e_reasoning(self):
        out = list(client.chat_stream(self.url, "", [{"role": "user", "content": "oi"}]))
        self.assertEqual(out, [("reasoning", "hmm"), ("content", "Olá"), ("content", " mundo")])
        self.assertNotIn("chat_template_kwargs", self.seen["body"])

    def test_chave_e_sem_pensar(self):
        list(client.chat_stream(self.url, "segredo", [], think=False))
        self.assertEqual(self.seen["auth"], "Bearer segredo")
        self.assertEqual(self.seen["body"]["chat_template_kwargs"], {"enable_thinking": False})

    def test_health(self):
        self.assertTrue(client.health(self.url, "k"))
        self.assertEqual(self.seen["auth"], "Bearer k")
        self.srv.shutdown()
        self.srv.server_close()
        self.assertFalse(client.health(self.url))

    def test_erro_de_rede(self):
        self.srv.shutdown()
        self.srv.server_close()
        with self.assertRaises(client.BackendError):
            list(client.chat_stream(self.url, "", []))


class ConfigAndFallbackTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patch = mock.patch.dict(os.environ, {"LLM_HOME": tmp.name})
        patch.start()
        self.addCleanup(patch.stop)
        from llm import config
        self.config = importlib.reload(config)
        self.addCleanup(importlib.reload, config)

    def test_config(self):
        cfg = self.config.load()
        self.assertEqual(cfg["backend"], "auto")
        self.assertEqual(cfg["porta_local"], 8080)
        cfg["colab_url"] = "http://x"
        self.config.save(cfg)
        self.assertEqual(self.config.load()["colab_url"], "http://x")

    def test_fallback_colab_para_local(self):
        from llm import __main__ as cli
        seen = {}
        srv, local_url = make_server([{"content": "do local"}], seen)
        self.addCleanup(srv.shutdown)
        state = {"backend": ("colab", "http://127.0.0.1:9", "k")}  # porta fechada
        msgs = [{"role": "user", "content": "oi"}]
        with mock.patch.object(cli.local, "ensure_running", return_value=local_url), \
                contextlib.redirect_stdout(io.StringIO()):
            texto = cli.answer({}, state, msgs, True)
        self.assertEqual(texto, "do local")
        self.assertEqual(state["backend"][0], "local")
        self.assertEqual(seen["body"]["messages"], msgs)  # histórico reenviado


class ArquivosTest(unittest.TestCase):
    def test_ler_salvar_e_bloqueio_fora_da_pasta(self):
        from llm import arquivos
        with tempfile.TemporaryDirectory() as base:
            arquivos.salvar(base, "notas/a.txt", "olá")
            texto, nomes = arquivos.ler(base, "notas")
            self.assertEqual(nomes, ["a.txt"])
            self.assertIn("olá", texto)
            self.assertIn("olá", arquivos.ler(base, "notas/a.txt")[0])
            with self.assertRaises(ValueError):
                arquivos.ler(base, "..")
            with self.assertRaises(ValueError):
                arquivos.salvar(base, "../fora.txt", "x")
            with self.assertRaises(ValueError):
                arquivos.salvar(base, "script.bat", "x")


if __name__ == "__main__":
    unittest.main()
