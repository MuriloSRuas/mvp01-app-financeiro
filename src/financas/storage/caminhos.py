"""Onde o banco de dados fica em cada sistema operacional.

É o **único** lugar do projeto que sabe se está no Linux ou no Windows
(RNF04). Todo o resto recebe um `Path` pronto e não precisa saber.

    Linux:   ~/.local/share/financas/financas.db   (ou $XDG_DATA_HOME/financas/)
    Windows: %APPDATA%\\financas\\financas.db

A pasta de dados do usuário é o lugar padrão de cada sistema para programas
guardarem dados; ela não some ao atualizar o programa e não polui a pasta
pessoal.
"""

import os
import sys
from collections.abc import Mapping
from pathlib import Path

NOME_PASTA = "financas"
NOME_BANCO = "financas.db"


def pasta_dados(
    sistema: str = sys.platform,
    ambiente: Mapping[str, str] = os.environ,
    casa: Path | None = None,
) -> Path:
    """Pasta de dados do programa para o sistema informado.

    Os parâmetros têm valores padrão (o sistema atual); eles existem para os
    testes conseguirem simular o Windows rodando no Linux.
    """
    casa = casa or Path.home()
    if sistema == "win32":
        base = Path(ambiente.get("APPDATA") or casa / "AppData" / "Roaming")
    else:
        base = Path(ambiente.get("XDG_DATA_HOME") or casa / ".local" / "share")
    return base / NOME_PASTA


def caminho_banco() -> Path:
    """Caminho do arquivo do banco no sistema atual (a pasta pode ainda não existir)."""
    return pasta_dados() / NOME_BANCO
