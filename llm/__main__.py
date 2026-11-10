import argparse
import sys

from . import client, config, local


def pick(cfg, force_local=False):
    """Retorna (nome, base_url, key)."""
    b = "local" if force_local else cfg["backend"]
    if b != "local" and cfg["colab_url"] and client.health(cfg["colab_url"], cfg["colab_key"]):
        return "colab", cfg["colab_url"], cfg["colab_key"]
    if b == "colab":
        print("Colab não responde; usando local.")
    return "local", local.ensure_running(cfg), ""


def answer(cfg, state, messages, think):
    """Envia o histórico e imprime a resposta; com fallback Colab -> local. Retorna o texto."""
    while True:
        nome, url, key = state["backend"]
        texto, pensando = [], False
        try:
            for kind, piece in client.chat_stream(url, key, messages, think):
                if kind == "reasoning":
                    if not pensando:
                        print("pensando...", end="\r", flush=True)
                        pensando = True
                else:
                    if pensando:
                        print(" " * 12, end="\r")
                        pensando = False
                    texto.append(piece)
                    print(piece, end="", flush=True)
            print()
            return "".join(texto)
        except client.BackendError as e:
            if nome != "colab":
                raise
            print("\nColab falhou (%s); trocando para local e reenviando o histórico." % e)
            state["backend"] = ("local", local.ensure_running(cfg), "")


def chat(args):
    cfg = config.load()
    think = not args.sem_pensar
    try:
        state = {"backend": pick(cfg, args.local)}
    except client.BackendError as e:
        sys.exit(str(e))
    print("Backend: %s. Comandos: /sair /limpar /backend /pensar" % state["backend"][0])
    messages = []
    while True:
        try:
            msg = input("você> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not msg:
            continue
        if msg == "/sair":
            return
        if msg == "/limpar":
            messages.clear()
            print("Histórico zerado.")
        elif msg == "/backend":
            print("Em uso:", state["backend"][0])
        elif msg == "/pensar":
            think = not think
            print("Thinking:", "ligado" if think else "desligado")
        else:
            messages.append({"role": "user", "content": msg})
            try:
                messages.append({"role": "assistant", "content": answer(cfg, state, messages, think)})
            except KeyboardInterrupt:
                print("\n[resposta interrompida]")
                messages.pop()
            except client.BackendError as e:
                print("Erro:", e)
                messages.pop()


def status(args):
    cfg = config.load()
    print("Backend configurado:", cfg["backend"])
    if cfg["colab_url"]:
        ok = client.health(cfg["colab_url"], cfg["colab_key"])
        print("Colab:", "respondendo" if ok else "não responde", "(%s)" % cfg["colab_url"])
    else:
        print("Colab: não configurado")
    print("Local:", "respondendo" if client.health("http://127.0.0.1:%d" % cfg["porta_local"]) else "parado")


def colab(args):
    cfg = config.load()
    if args.limpar:
        cfg.update(colab_url="", colab_key="")
        config.save(cfg)
        return print("Colab removido da configuração.")
    if not (args.url and args.chave):
        sys.exit("Uso: llm colab <url> <chave>  ou  llm colab --limpar")
    cfg.update(colab_url=args.url.rstrip("/"), colab_key=args.chave)
    config.save(cfg)
    ok = client.health(cfg["colab_url"], cfg["colab_key"])
    print("Salvo. Colab", "respondendo." if ok else "NÃO respondeu ao /health (o fallback local continua valendo).")


def setbackend(nome):
    def f(args):
        cfg = config.load()
        cfg["backend"] = nome
        config.save(cfg)
        print("Backend:", nome)
    return f


def parar(args):
    print("Servidor local parado." if local.stop() else "Nenhum servidor local registrado.")


def main():
    p = argparse.ArgumentParser(prog="llm")
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("chat")
    c.add_argument("--sem-pensar", action="store_true")
    c.add_argument("--local", action="store_true")
    c.set_defaults(f=chat)
    sub.add_parser("status").set_defaults(f=status)
    k = sub.add_parser("colab")
    k.add_argument("url", nargs="?")
    k.add_argument("chave", nargs="?")
    k.add_argument("--limpar", action="store_true")
    k.set_defaults(f=colab)
    sub.add_parser("local").set_defaults(f=setbackend("local"))
    sub.add_parser("auto").set_defaults(f=setbackend("auto"))
    sub.add_parser("parar").set_defaults(f=parar)
    args = p.parse_args()
    if not args.cmd:
        args = p.parse_args(["chat"])
    args.f(args)


if __name__ == "__main__":
    main()
