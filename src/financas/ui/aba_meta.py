"""Aba "Meta de economia": formulário do RF01/RF02 e relatório.

Esta aba não faz conta nenhuma: lê os campos, chama o core e mostra o
relatório. Toda regra está em `core/meta_economia.py`.
"""

import tkinter as tk
from datetime import datetime
from decimal import Decimal
from tkinter import ttk

from financas.core.dinheiro import ler_dinheiro, ler_inteiro, ler_taxa_percentual
from financas.core.meta_economia import calcular_aporte, calcular_meses
from financas.reports.markdown import relatorio_aporte, relatorio_meses
from financas.ui.componentes import AbaCalculo, criar_campo, habilitar, ler_campo

MESES = "meses"
APORTE = "aporte"


class AbaMeta(AbaCalculo):
    def __init__(self, pai: tk.Misc) -> None:
        super().__init__(pai)
        f = self.formulario

        # Qual pergunta responder. A variável guarda "meses" ou "aporte" e
        # avisa (command=) quando o usuário troca a opção.
        self.modo = tk.StringVar(value=MESES)
        ttk.Label(f, text="O que você quer descobrir?").grid(row=0, column=0, sticky="w", pady=(0, 4))
        opcoes = ttk.Frame(f)
        opcoes.grid(row=0, column=1, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Radiobutton(
            opcoes, text="Em quantos meses chego à meta", variable=self.modo, value=MESES,
            command=self._atualizar_modo,
        ).pack(side="left")
        ttk.Radiobutton(
            opcoes, text="Quanto guardar por mês", variable=self.modo, value=APORTE,
            command=self._atualizar_modo,
        ).pack(side="left", padx=(12, 0))

        self.campo_meta = criar_campo(f, 1, "Valor da meta (R$)", "ex.: 10.000,00")
        self.campo_aporte = criar_campo(f, 2, "Aporte mensal (R$)", "quanto você guarda no fim de cada mês")
        self.campo_prazo = criar_campo(f, 3, "Prazo (meses)", "número inteiro, até 1200")
        self.campo_taxa = criar_campo(f, 4, "Rentabilidade (% ao mês)", "opcional: vazio = 0%")

        self.ligar_enter(self.campo_meta, self.campo_aporte, self.campo_prazo, self.campo_taxa)
        self._atualizar_modo()

    def _atualizar_modo(self) -> None:
        """Mostra como editável só o campo que faz sentido para a pergunta escolhida."""
        por_meses = self.modo.get() == MESES
        habilitar(self.campo_aporte, por_meses)
        habilitar(self.campo_prazo, not por_meses)

    def gerar_relatorio(self, momento: datetime) -> tuple[str, str]:
        meta = ler_campo(self.campo_meta, ler_dinheiro, "Valor da meta")
        taxa = self._ler_taxa()
        if self.modo.get() == MESES:
            aporte = ler_campo(self.campo_aporte, ler_dinheiro, "Aporte mensal")
            texto = relatorio_meses(calcular_meses(meta, aporte, taxa), momento)
        else:
            prazo = ler_campo(self.campo_prazo, ler_inteiro, "Prazo em meses")
            texto = relatorio_aporte(calcular_aporte(meta, prazo, taxa), momento)
        return texto, "meta-economia"

    def _ler_taxa(self) -> Decimal:
        # RF01: a taxa é opcional e vale 0% quando não informada.
        if not self.campo_taxa.get().strip():
            return Decimal(0)
        return ler_campo(self.campo_taxa, ler_taxa_percentual, "Rentabilidade")
