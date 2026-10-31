"""Janela principal: cria a janela, as abas e entrega o controle ao Tkinter.

A aba "Gastos" entra na Fase 5.
"""

import sys
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from financas.ui.aba_antecipacao import AbaAntecipacao
from financas.ui.aba_meta import AbaMeta


def criar_janela() -> tk.Tk:
    """Monta a janela com as abas, sem abri-la ainda (quem abre é `mainloop`)."""
    janela = tk.Tk()
    janela.title("Finanças")
    janela.geometry("960x720")
    janela.minsize(720, 520)
    _escolher_tema(janela)
    _tratar_erros_inesperados(janela)

    abas = ttk.Notebook(janela)
    abas.add(AbaMeta(abas), text="Meta de economia")
    abas.add(AbaAntecipacao(abas), text="Antecipação de parcelas")
    abas.pack(fill="both", expand=True, padx=8, pady=8)
    return janela


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
