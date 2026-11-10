import json
import urllib.request


class BackendError(Exception):
    pass


def _headers(key):
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = "Bearer " + key
    return h


def health(base_url, key=""):
    try:
        req = urllib.request.Request(base_url.rstrip("/") + "/health", headers=_headers(key))
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def chat_stream(base_url, key, messages, think=True):
    """Gera tuplas ("reasoning"|"content", texto)."""
    body = {"messages": messages, "stream": True}
    if not think:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(base_url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers=_headers(key))
    try:
        with urllib.request.urlopen(req, timeout=300) as r:  # prefill longo na CPU passa de 60 s sem bytes
            for raw in r:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                choices = json.loads(data).get("choices") or [{}]
                delta = choices[0].get("delta", {})
                if delta.get("reasoning_content"):
                    yield "reasoning", delta["reasoning_content"]
                if delta.get("content"):
                    yield "content", delta["content"]
    except (OSError, ValueError) as e:  # URLError, timeout, conexão cortada, JSON ruim
        raise BackendError(str(e)) from e
