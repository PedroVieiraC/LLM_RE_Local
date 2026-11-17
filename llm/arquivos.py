from pathlib import Path

LIMITE = 200_000  # caracteres por /ler; evita estourar o contexto de 16k tokens


def _dentro(base, nome):
    base = Path(base).resolve()
    alvo = (base / nome).resolve()
    if alvo != base and base not in alvo.parents:
        raise ValueError("Fora da pasta permitida: %s" % base)
    return alvo


def ler(base, nome=""):
    """Texto de um arquivo, ou de todos os arquivos de uma pasta (não recursivo), dentro de base."""
    alvo = _dentro(base, nome)
    arquivos = sorted(f for f in alvo.iterdir() if f.is_file()) if alvo.is_dir() else [alvo]
    partes = []
    for f in arquivos:
        try:
            partes.append("=== %s ===\n%s" % (f.name, f.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            partes.append("=== %s === (binário, ignorado)" % f.name)
    texto = "\n\n".join(partes) or "(pasta vazia)"
    return texto[:LIMITE], [f.name for f in arquivos]


def salvar(base, nome, texto):
    if not nome.lower().endswith(".txt"):
        raise ValueError("Só arquivos .txt")
    alvo = _dentro(base, nome)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(texto, encoding="utf-8")
    return alvo
