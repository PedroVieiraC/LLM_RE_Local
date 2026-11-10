import json
import os
from pathlib import Path

HOME = Path(os.environ.get("LLM_HOME") or Path.home() / ".llm")


def _defaults():
    return {
        "backend": "auto",
        "colab_url": "",
        "colab_key": "",
        "modelo_local": str(HOME / "models" / "DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf"),
        "porta_local": 8080,
    }


def load():
    cfg = _defaults()
    f = HOME / "config.json"
    if f.exists():
        cfg.update(json.loads(f.read_text(encoding="utf-8")))
    return cfg


def save(cfg):
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
