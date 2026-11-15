"""Converte um `Documento` em Markdown, para salvar em arquivo `.md` (RF06).

A tela não usa este módulo: ela desenha o `Documento` direto, já formatado.
O Markdown só é gerado quando o usuário clica em "Salvar relatório (.md)",
para abrir o arquivo no Obsidian ou em outro leitor de Markdown.
"""

from financas.reports.documento import (
    Aviso,
    Bloco,
    Documento,
    Formula,
    Paragrafo,
    Passos,
    Secao,
    Tabela,
    Texto,
    Trecho,
)


def para_markdown(documento: Documento) -> str:
    """Texto Markdown completo: título, data e os blocos separados por linha em branco."""
    momento = documento.gerado_em
    partes = [
        f"# {documento.titulo}",
        f"Gerado em {momento:%d/%m/%Y} às {momento:%H:%M}.",
        *(_bloco(b) for b in documento.blocos),
    ]
    return "\n\n".join(partes) + "\n"


def _bloco(bloco: Bloco) -> str:
    match bloco:
        case Secao(titulo):
            return f"## {titulo}"
        case Paragrafo(conteudo):
            return _texto(conteudo)
        case Formula(linhas):
            return "\n".join(["```text", *linhas, "```"])
        case Tabela():
            return "\n".join(_tabela(bloco))
        case Passos(itens):
            return "\n".join(f"{n}. {_texto(item)}" for n, item in enumerate(itens, start=1))
        case Aviso(conteudo):
            # "> [!warning]" vira um quadro de alerta no Obsidian; em outros leitores
            # de Markdown aparece como uma citação comum, que também funciona.
            return f"> [!warning] Aviso\n> {_texto(conteudo)}"
    raise TypeError(f"bloco desconhecido: {bloco!r}")  # pragma: no cover (proteção contra bloco novo esquecido)


def _texto(conteudo: Texto) -> str:
    return "".join(_trecho(t) for t in conteudo)


def _trecho(trecho: Trecho) -> str:
    texto = _escapar(trecho.texto)
    if trecho.codigo:
        return f"`{texto}`"
    if trecho.negrito:
        return f"**{texto}**"
    if trecho.italico:
        return f"_{texto}_"
    return texto


def _escapar(texto: str) -> str:
    # Uma "|" digitada pelo usuário quebraria a tabela; "\|" é a barra literal.
    return texto.replace("|", "\\|")


def _tabela(tabela: Tabela) -> list[str]:
    """Tabela Markdown com colunas alinhadas por espaços.

    O alinhamento não muda nada no Obsidian (ele ignora os espaços extras),
    mas deixa o arquivo legível também em um editor de texto comum.
    """
    corpo = [[_escapar(c) for c in linha] for linha in tabela.linhas]
    if tabela.destacar_ultima and corpo:
        corpo[-1] = [f"**{c}**" if c else c for c in corpo[-1]]
    cabecalhos = list(tabela.cabecalhos)
    larguras = [
        max(3, len(cabecalho), *(len(celulas[coluna]) for celulas in corpo))
        for coluna, cabecalho in enumerate(cabecalhos)
    ]

    def linha(celulas: list[str]) -> str:
        return "| " + " | ".join(c.ljust(l) for c, l in zip(celulas, larguras)) + " |"

    separador = "| " + " | ".join("-" * l for l in larguras) + " |"
    return [linha(cabecalhos), separador, *(linha(celulas) for celulas in corpo)]
