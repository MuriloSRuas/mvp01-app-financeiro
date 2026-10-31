"""Salvar relatórios em arquivo `.md` (RF06).

Fica separado de `markdown.py` de propósito: lá só se monta texto; aqui se
mexe no disco. A janela pergunta onde salvar e chama estas funções.

Usa `pathlib`, que funciona igual no Linux e no Windows (RNF04).
"""

from datetime import datetime
from pathlib import Path


def nome_arquivo(prefixo: str, momento: datetime) -> str:
    """Nome sugerido: "meta-economia-2026-10-31-1405.md".

    Data no formato ano-mês-dia para os arquivos ficarem em ordem cronológica
    quando listados por nome (no Obsidian ou no gerenciador de arquivos).
    """
    return f"{prefixo}-{momento:%Y-%m-%d-%H%M}.md"


def salvar_relatorio(texto: str, caminho: Path) -> Path:
    """Grava o relatório em UTF-8 e devolve o caminho final.

    Se o nome não terminar em ".md", a extensão é acrescentada, para o
    Obsidian reconhecer o arquivo como nota.
    """
    if caminho.suffix.lower() != ".md":
        caminho = caminho.with_name(caminho.name + ".md")
    # newline="\n": mesma quebra de linha no Linux e no Windows.
    caminho.write_text(texto, encoding="utf-8", newline="\n")
    return caminho
