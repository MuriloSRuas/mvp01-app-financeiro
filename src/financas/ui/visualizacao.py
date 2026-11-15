"""Desenha um `Documento` (relatório) numa caixa de texto do Tkinter.

A tela mostra as contas já formatadas: títulos maiores, negrito, fórmulas em
destaque, tabelas com colunas alinhadas (valores à direita) e o aviso em
amarelo. Nenhum símbolo de Markdown aparece aqui; o Markdown só existe no
arquivo, quando o usuário pede para salvar.

Como funciona: o `tk.Text` aceita "tags", que são estilos com nome (fonte,
cor, margem). Cada pedaço de texto é inserido com as tags do seu estilo.
"""

import re
import tkinter as tk
from tkinter import font as tkfont

from financas.reports.documento import (
    Aviso,
    Documento,
    Formula,
    Paragrafo,
    Passos,
    Secao,
    Tabela,
    Texto,
)

COR_TITULO = "#1f3a5f"
COR_SECAO = "#1f3a5f"
COR_SUAVE = "gray40"
FUNDO_FORMULA = "#eef2f7"
FUNDO_AVISO = "#fff4ce"
FUNDO_DESTAQUE = "#e8f1e8"

# Células que são número, valor em reais ou percentual ficam alinhadas à direita.
_NUMERO = re.compile(r"-?(R\$ )?[\d.,]+%?")


def configurar_estilos(area: tk.Text) -> None:
    """Cria as tags de estilo. Chamar uma vez, logo depois de criar a caixa."""
    base = tkfont.nametofont("TkDefaultFont").actual()
    fixa = tkfont.nametofont("TkFixedFont").actual()
    familia, tamanho = base["family"], abs(base["size"]) or 10
    familia_fixa, tamanho_fixa = fixa["family"], abs(fixa["size"]) or 10

    area.configure(font=(familia, tamanho), wrap="word")
    area.tag_configure("titulo", font=(familia, tamanho + 6, "bold"), foreground=COR_TITULO, spacing3=2)
    area.tag_configure("gerado_em", foreground=COR_SUAVE, spacing3=6)
    area.tag_configure("secao", font=(familia, tamanho + 2, "bold"), foreground=COR_SECAO, spacing1=14, spacing3=4)
    area.tag_configure("paragrafo", spacing1=3, spacing3=3)
    area.tag_configure("negrito", font=(familia, tamanho, "bold"))
    area.tag_configure("italico", font=(familia, tamanho, "italic"), foreground=COR_SUAVE)
    area.tag_configure("codigo", font=(familia_fixa, tamanho_fixa))
    area.tag_configure(
        "formula", font=(familia_fixa, tamanho_fixa + 1), background=FUNDO_FORMULA,
        lmargin1=16, lmargin2=16, rmargin=16, spacing1=2, spacing3=2, wrap="none",
    )
    area.tag_configure("passo", lmargin1=12, lmargin2=32, spacing1=2, spacing3=2)
    # Tabelas não quebram linha: colunas alinhadas; usa-se a barra horizontal.
    area.tag_configure("tabela", font=(familia_fixa, tamanho_fixa), lmargin1=4, wrap="none")
    area.tag_configure("tabela_cabecalho", font=(familia_fixa, tamanho_fixa, "bold"))
    area.tag_configure("tabela_regua", foreground="gray60")
    area.tag_configure("tabela_destaque", font=(familia_fixa, tamanho_fixa, "bold"), background=FUNDO_DESTAQUE)
    area.tag_configure(
        "aviso", background=FUNDO_AVISO, lmargin1=10, lmargin2=10, rmargin=10, spacing1=6, spacing3=6,
    )
    # Ordem de prioridade: a última criada vence quando duas definem a mesma opção.
    area.tag_raise("negrito")
    area.tag_raise("italico")
    area.tag_raise("codigo")


def desenhar(area: tk.Text, documento: Documento) -> None:
    """Apaga a caixa e escreve o relatório formatado."""
    area.configure(state="normal")
    area.delete("1.0", "end")

    gerado = documento.gerado_em
    area.insert("end", documento.titulo + "\n", "titulo")
    area.insert("end", f"Gerado em {gerado:%d/%m/%Y} às {gerado:%H:%M}.\n", "gerado_em")

    for bloco in documento.blocos:
        match bloco:
            case Secao(titulo):
                area.insert("end", titulo + "\n", "secao")
            case Paragrafo(conteudo):
                _inserir_texto(area, conteudo, "paragrafo")
                area.insert("end", "\n", "paragrafo")
            case Formula(linhas):
                area.insert("end", "\n".join(linhas) + "\n", "formula")
            case Passos(itens):
                for numero, item in enumerate(itens, start=1):
                    area.insert("end", f"{numero}. ", ("passo", "negrito"))
                    _inserir_texto(area, item, "passo")
                    area.insert("end", "\n", "passo")
            case Tabela():
                _inserir_tabela(area, bloco)
            case Aviso(conteudo):
                area.insert("end", "⚠ Aviso: ", ("aviso", "negrito"))
                _inserir_texto(area, conteudo, "aviso")
                area.insert("end", "\n", "aviso")

    area.configure(state="disabled")


def mostrar_mensagem(area: tk.Text, mensagem: str) -> None:
    """Texto simples (ex.: instrução antes do primeiro cálculo)."""
    area.configure(state="normal")
    area.delete("1.0", "end")
    area.insert("1.0", mensagem, "italico")
    area.configure(state="disabled")


def _inserir_texto(area: tk.Text, conteudo: Texto, estilo: str) -> None:
    for trecho in conteudo:
        tags = [estilo]
        if trecho.negrito:
            tags.append("negrito")
        if trecho.italico:
            tags.append("italico")
        if trecho.codigo:
            tags.append("codigo")
        area.insert("end", trecho.texto, tuple(tags))


def _inserir_tabela(area: tk.Text, tabela: Tabela) -> None:
    colunas = range(len(tabela.cabecalhos))
    larguras = [
        max(len(tabela.cabecalhos[c]), *(len(linha[c]) for linha in tabela.linhas)) for c in colunas
    ]
    a_direita = [
        any(linha[c] for linha in tabela.linhas)
        and all(not linha[c] or _NUMERO.fullmatch(linha[c]) for linha in tabela.linhas)
        for c in colunas
    ]

    def formatar(celulas: tuple[str, ...]) -> str:
        partes = [
            celula.rjust(largura) if direita else celula.ljust(largura)
            for celula, largura, direita in zip(celulas, larguras, a_direita)
        ]
        return "  " + "   ".join(partes).rstrip() + "\n"

    regua = "  " + "   ".join("─" * l for l in larguras) + "\n"

    area.insert("end", "\n", "tabela")
    if any(tabela.cabecalhos):
        area.insert("end", formatar(tabela.cabecalhos), ("tabela", "tabela_cabecalho"))
        area.insert("end", regua, ("tabela", "tabela_regua"))
    ultima = len(tabela.linhas) - 1
    for numero, linha in enumerate(tabela.linhas):
        if tabela.destacar_ultima and numero == ultima:
            area.insert("end", regua, ("tabela", "tabela_regua"))
            area.insert("end", formatar(linha), ("tabela", "tabela_destaque"))
        else:
            area.insert("end", formatar(linha), "tabela")
    area.insert("end", "\n", "tabela")
