"""Aba "Antecipação de parcelas": formulário do RF03/RF04 e relatório.

Como na aba de meta, aqui só se lê os campos e se chama o core
(`core/antecipacao.py`); nenhuma conta é feita na interface.
"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from financas.core.antecipacao import antecipar_com_valor, antecipar_quantidade
from financas.core.dinheiro import ler_dinheiro, ler_inteiro, ler_taxa_percentual
from financas.reports.markdown import relatorio_antecipacao
from financas.ui.componentes import AbaCalculo, criar_campo, habilitar, ler_campo

QUANTIDADE = "quantidade"
VALOR = "valor"


class AbaAntecipacao(AbaCalculo):
    def __init__(self, pai: tk.Misc) -> None:
        super().__init__(pai)
        f = self.formulario

        self.campo_parcela = criar_campo(f, 0, "Valor da parcela (R$)", "parcelas iguais")
        self.campo_taxa = criar_campo(f, 1, "Juros do contrato (% ao mês)", "ex.: 2 ou 1,99")
        self.campo_restantes = criar_campo(
            f, 2, "Parcelas restantes", "sem contar a que você paga agora"
        )

        self.modo = tk.StringVar(value=QUANTIDADE)
        ttk.Label(f, text="Como quer antecipar?").grid(row=3, column=0, sticky="w", pady=(10, 4))
        opcoes = ttk.Frame(f)
        opcoes.grid(row=3, column=1, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Radiobutton(
            opcoes, text="Informar quantas parcelas", variable=self.modo, value=QUANTIDADE,
            command=self._atualizar_modo,
        ).pack(side="left")
        ttk.Radiobutton(
            opcoes, text="Informar quanto tenho disponível", variable=self.modo, value=VALOR,
            command=self._atualizar_modo,
        ).pack(side="left", padx=(12, 0))

        self.campo_quantidade = criar_campo(f, 4, "Parcelas a antecipar", "as últimas, da última para trás")
        self.campo_valor = criar_campo(f, 5, "Valor disponível (R$)", "quanto você pode pagar hoje")

        self.ligar_enter(
            self.campo_parcela, self.campo_taxa, self.campo_restantes,
            self.campo_quantidade, self.campo_valor,
        )
        self._atualizar_modo()

    def _atualizar_modo(self) -> None:
        por_quantidade = self.modo.get() == QUANTIDADE
        habilitar(self.campo_quantidade, por_quantidade)
        habilitar(self.campo_valor, not por_quantidade)

    def gerar_relatorio(self, momento: datetime) -> tuple[str, str]:
        parcela = ler_campo(self.campo_parcela, ler_dinheiro, "Valor da parcela")
        taxa = ler_campo(self.campo_taxa, ler_taxa_percentual, "Juros do contrato")
        restantes = ler_campo(self.campo_restantes, ler_inteiro, "Parcelas restantes")
        if self.modo.get() == QUANTIDADE:
            quantidade = ler_campo(self.campo_quantidade, ler_inteiro, "Parcelas a antecipar")
            resultado = antecipar_quantidade(parcela, taxa, restantes, quantidade)
        else:
            valor = ler_campo(self.campo_valor, ler_dinheiro, "Valor disponível")
            resultado = antecipar_com_valor(parcela, taxa, restantes, valor)
        return relatorio_antecipacao(resultado, momento), "antecipacao-parcelas"
