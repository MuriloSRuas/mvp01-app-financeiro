"""Peças de interface usadas pelas abas de cálculo.

As duas calculadoras têm o mesmo esqueleto: campos com rótulo, botão
Calcular, área com o relatório e botão "Salvar relatório (.md)". Em vez de
repetir esse código em cada aba, ele fica aqui.
"""

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TypeVar

from financas.core.dinheiro import ErroDeValidacao
from financas.reports.arquivo import nome_arquivo, salvar_relatorio

T = TypeVar("T")


def criar_campo(pai: ttk.Frame, linha: int, rotulo: str, dica: str = "") -> ttk.Entry:
    """Cria, na linha `linha` da grade, um rótulo, uma caixa de texto e uma dica.

    Layout em grade (grid), três colunas:  Rótulo | [ caixa ] | dica em cinza
    """
    ttk.Label(pai, text=rotulo).grid(row=linha, column=0, sticky="w", padx=(0, 8), pady=3)
    campo = ttk.Entry(pai, width=18)
    campo.grid(row=linha, column=1, sticky="w", pady=3)
    if dica:
        ttk.Label(pai, text=dica, foreground="gray40").grid(row=linha, column=2, sticky="w", padx=(8, 0))
    return campo


def habilitar(campo: ttk.Entry, ativo: bool) -> None:
    """Liga ou desliga uma caixa de texto (desligada fica cinza e não aceita digitação)."""
    campo.state(["!disabled"] if ativo else ["disabled"])


def ler_campo(campo: ttk.Entry, ler: Callable[[str, str], T], nome: str) -> T:
    """Lê o texto da caixa com a função `ler` (ex.: `ler_dinheiro`).

    Se o valor for inválido, coloca o cursor na caixa com problema antes de
    repassar o erro, para o usuário saber o que corrigir.
    """
    try:
        return ler(campo.get(), nome)
    except ErroDeValidacao:
        campo.focus_set()
        campo.select_range(0, "end")
        raise


def mostrar_erro(pai: tk.Misc, erro: Exception) -> None:
    """Mostra um erro de validação numa caixa de mensagem, sem stack trace."""
    messagebox.showerror("Verifique os dados", str(erro), parent=pai)


class PainelRelatorio(ttk.Frame):
    """Área de texto (só leitura) com o relatório e o botão "Salvar relatório (.md)".

    Guarda o último relatório gerado. É esse texto, igual ao que aparece na
    tela, que vai para o arquivo.
    """

    def __init__(self, pai: tk.Misc) -> None:
        super().__init__(pai)
        self._texto_atual = ""
        self._nome_sugerido = ""
        self._ultima_pasta = Path.home()

        self.botao_salvar = ttk.Button(self, text="Salvar relatório (.md)", command=self.salvar)
        self.botao_salvar.state(["disabled"])  # só depois do primeiro cálculo
        self.botao_salvar.pack(side="bottom", anchor="e", pady=(6, 0))

        moldura = ttk.Frame(self)
        moldura.pack(side="top", fill="both", expand=True)
        # wrap="none": linhas longas (tabelas) não quebram; usa-se a barra horizontal.
        self.area = tk.Text(moldura, font="TkFixedFont", wrap="none", height=20, padx=8, pady=8)
        rolagem_v = ttk.Scrollbar(moldura, orient="vertical", command=self.area.yview)
        rolagem_h = ttk.Scrollbar(moldura, orient="horizontal", command=self.area.xview)
        self.area.configure(yscrollcommand=rolagem_v.set, xscrollcommand=rolagem_h.set)
        self.area.grid(row=0, column=0, sticky="nsew")
        rolagem_v.grid(row=0, column=1, sticky="ns")
        rolagem_h.grid(row=1, column=0, sticky="ew")
        moldura.rowconfigure(0, weight=1)
        moldura.columnconfigure(0, weight=1)

        self._escrever("Preencha os dados acima e clique em Calcular.\n")

    def mostrar(self, texto: str, nome_sugerido: str) -> None:
        """Exibe um novo relatório e libera o botão de salvar."""
        self._texto_atual = texto
        self._nome_sugerido = nome_sugerido
        self._escrever(texto)
        self.botao_salvar.state(["!disabled"])

    def salvar(self) -> None:
        """Pergunta onde salvar e grava o relatório (RF06)."""
        escolhido = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar relatório",
            initialdir=self._ultima_pasta,
            initialfile=self._nome_sugerido,
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Todos os arquivos", "*")],
        )
        if not escolhido:  # usuário cancelou
            return
        try:
            caminho = salvar_relatorio(self._texto_atual, Path(escolhido))
        except OSError as erro:
            messagebox.showerror("Não foi possível salvar", f"{escolhido}\n\n{erro.strerror}", parent=self)
            return
        self._ultima_pasta = caminho.parent
        messagebox.showinfo("Relatório salvo", f"Salvo em:\n{caminho}", parent=self)

    def _escrever(self, texto: str) -> None:
        # O Text precisa estar "normal" para receber texto; depois volta a só leitura.
        self.area.configure(state="normal")
        self.area.delete("1.0", "end")
        self.area.insert("1.0", texto)
        self.area.configure(state="disabled")


class AbaCalculo(ttk.Frame):
    """Esqueleto de uma aba de cálculo: formulário em cima, relatório embaixo.

    Cada aba concreta (meta, antecipação) monta seus campos em
    `self.formulario` e implementa `gerar_relatorio`, que lê os campos,
    chama o core e devolve (texto do relatório, prefixo do nome do arquivo).
    """

    def __init__(self, pai: tk.Misc) -> None:
        super().__init__(pai, padding=12)
        self.formulario = ttk.Frame(self)
        self.formulario.pack(side="top", fill="x")
        self.botao_calcular = ttk.Button(self, text="Calcular", command=self.calcular)
        self.botao_calcular.pack(side="top", anchor="w", pady=10)
        self.painel = PainelRelatorio(self)
        self.painel.pack(side="top", fill="both", expand=True)

    def ligar_enter(self, *campos: ttk.Entry) -> None:
        """Enter em qualquer campo equivale a clicar em Calcular."""
        for campo in campos:
            campo.bind("<Return>", lambda _evento: self.calcular())

    def calcular(self) -> None:
        momento = datetime.now()
        try:
            texto, prefixo = self.gerar_relatorio(momento)
        except ErroDeValidacao as erro:
            mostrar_erro(self, erro)
            return
        self.painel.mostrar(texto, nome_arquivo(prefixo, momento))

    def gerar_relatorio(self, momento: datetime) -> tuple[str, str]:
        raise NotImplementedError
