"""Janela principal: cria a janela, as abas e entrega o controle ao Tkinter."""

import sqlite3
import sys
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import messagebox, ttk

from financas.storage.caminhos import caminho_banco
from financas.storage.repositorio import RepositorioLancamentos
from financas.ui.aba_antecipacao import AbaAntecipacao
from financas.ui.aba_gastos import AbaGastos
from financas.ui.aba_meta import AbaMeta


def criar_janela(arquivo_banco: Path | str | None = None) -> tk.Tk:
    """Monta a janela com as abas, sem abri-la ainda (quem abre é `mainloop`).

    `arquivo_banco` existe para testes usarem um banco temporário; no uso
    normal fica `None` e o banco vai para a pasta de dados do usuário.
    """
    janela = tk.Tk()
    janela.title("Finanças")
    janela.geometry("1000x780")
    janela.minsize(860, 640)
    _escolher_tema(janela)
    _tratar_erros_inesperados(janela)

    abas = ttk.Notebook(janela)
    abas.add(AbaMeta(abas), text="Meta de economia")
    abas.add(AbaAntecipacao(abas), text="Antecipação de parcelas")
    _adicionar_aba_gastos(janela, abas, arquivo_banco or caminho_banco())
    abas.pack(fill="both", expand=True, padx=8, pady=8)
    return janela


def _adicionar_aba_gastos(janela: tk.Tk, abas: ttk.Notebook, arquivo_banco: Path | str) -> None:
    """Abre o banco e cria a aba Gastos.

    Se o banco não abrir (sem permissão na pasta, arquivo corrompido), as
    calculadoras continuam funcionando e o usuário vê o motivo.
    """
    try:
        repositorio = RepositorioLancamentos(arquivo_banco)
    except (OSError, sqlite3.Error) as erro:
        messagebox.showerror(
            "Gastos indisponíveis",
            f"Não foi possível abrir o banco de dados em:\n{arquivo_banco}\n\n{erro}\n\n"
            "As calculadoras continuam funcionando.",
            parent=janela,
        )
        return
    abas.add(AbaGastos(abas, repositorio), text="Gastos")

    def ao_fechar() -> None:
        repositorio.fechar()
        janela.destroy()

    # Ao clicar no X da janela: fecha o banco antes de sair.
    janela.protocol("WM_DELETE_WINDOW", ao_fechar)


def main() -> None:
    # mainloop() fica "escutando" cliques e teclas até a janela ser fechada.
    criar_janela().mainloop()


def _escolher_tema(janela: tk.Tk) -> None:
    # "clam" é o tema do ttk com melhor aparência no Linux; no Windows o
    # padrão do sistema ("vista") já é bom, então só trocamos se ele não existir.
    estilo = ttk.Style(janela)
    if "vista" not in estilo.theme_names() and "clam" in estilo.theme_names():
        estilo.theme_use("clam")


def _tratar_erros_inesperados(janela: tk.Tk) -> None:
    """Erro que ninguém previu (um bug) vira mensagem na tela, e o programa segue aberto.

    Erros de digitação já são tratados nas abas; isto é a última rede de
    proteção. O detalhe técnico vai para o terminal, para facilitar a correção.
    """

    def ao_ocorrer_erro(tipo, erro, rastro) -> None:
        traceback.print_exception(tipo, erro, rastro, file=sys.stderr)
        messagebox.showerror(
            "Erro inesperado",
            f"Algo deu errado, mas o programa continua aberto.\n\nDetalhe: {erro}",
            parent=janela,
        )

    janela.report_callback_exception = ao_ocorrer_erro
