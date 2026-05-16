import json, uuid
from datetime import datetime
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent / "dados"


def carregar(arquivo):
    caminho = PASTA_DADOS / arquivo
    if not caminho.exists():
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar(arquivo, dados):
    with open(PASTA_DADOS / arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, default=str)


def buscar_por_id(arquivo, registro_id):
    return next((r for r in carregar(arquivo) if r["id"] == registro_id), None)


def criar(arquivo, registro):
    dados = carregar(arquivo)
    registro.setdefault("id", str(uuid.uuid4())[:8])
    registro.setdefault("created_at", datetime.now().isoformat())
    dados.append(registro)
    salvar(arquivo, dados)
    return registro


def atualizar(arquivo, registro_id, campos):
    dados = carregar(arquivo)
    for r in dados:
        if r["id"] == registro_id:
            r.update(campos)
            salvar(arquivo, dados)
            return r
    return None
