import os
import subprocess
import sys
import time

from . import client, config


def ensure_running(cfg):
    url = "http://127.0.0.1:%d" % cfg["porta_local"]
    if client.health(url):
        return url
    exe = next(config.HOME.glob("bin/**/llama-server.exe"), None)
    modelo = cfg["modelo_local"]
    if not exe or not os.path.exists(modelo):
        raise client.BackendError("llama-server ou modelo local ausente; rode scripts\\instalar_local.ps1")
    config.HOME.mkdir(parents=True, exist_ok=True)
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    log_path = config.HOME / "llama-server.log"
    with open(log_path, "ab") as log:
        p = subprocess.Popen([str(exe), "-m", modelo, "--port", str(cfg["porta_local"]),
                              "--host", "127.0.0.1", "-c", "8192", "--jinja"],
                             stdout=log, stderr=log, stdin=subprocess.DEVNULL, creationflags=flags)
    (config.HOME / "server.pid").write_text(str(p.pid))
    print("Subindo servidor local (pode levar um tempo)...")
    fim = time.time() + 180
    while time.time() < fim:
        if client.health(url):
            return url
        if p.poll() is not None:
            raise client.BackendError("llama-server encerrou; veja " + str(log_path))
        time.sleep(2)
    raise client.BackendError("llama-server não respondeu em 180 s; veja " + str(log_path))


def stop():
    pidf = config.HOME / "server.pid"
    if not pidf.exists():
        return False
    pid = pidf.read_text().strip()
    pidf.unlink()
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", pid], capture_output=True)
    else:
        try:
            os.kill(int(pid), 15)
        except OSError:
            return False
    return True
