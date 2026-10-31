"""Aba "Gastos": lançar, listar por mês, editar, excluir e gerar relatório (RF07 a RF11).

Três blocos, de cima para baixo:

1. **Lançamento**: formulário para criar um lançamento ou editar o selecionado.
2. **Lançamentos do mês**: filtro por mês/ano, tabela e totais do mês.
3. **Relatório de gastos**: período (de/até) e botão que abre o relatório.

Como nas outras abas, nenhuma regra fica aqui: validação e contas estão em
`core/gastos.py`, e quem grava é o `RepositorioLancamentos`.
"""

import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

from financas.core.dinheiro import ErroDeValidacao, formatar_numero, formatar_reais, ler_dinheiro
from financas.core.gastos import (
    ENTRADA,
    SAIDA,
    Lancamento,
    formatar_data,
    ler_data,
    novo_lancamento,
    resumir,
)
from financas.reports.arquivo import nome_arquivo
from financas.reports.markdown import relatorio_gastos
from financas.storage.repositorio import RepositorioLancamentos, periodo_do_mes
from financas.ui.componentes import PainelRelatorio, ler_campo, mostrar_erro

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
COLUNAS = ("data", "tipo", "categoria", "descricao", "valor")


class AbaGastos(ttk.Frame):
    def __init__(self, pai: tk.Misc, repositorio: RepositorioLancamentos) -> None:
        super().__init__(pai, padding=12)
        self.repo = repositorio
        self._editando: Lancamento | None = None  # lançamento em edição, ou None
        self._lancamentos: dict[str, Lancamento] = {}  # linha da tabela -> lançamento

        self._montar_formulario()
        self._montar_lista()
        self._montar_relatorio()

        # A lista abre no mês atual. Isto é só navegação: nenhum dado é preenchido.
        hoje = date.today()
        self._mostrar_mes(hoje.year, hoje.month)
        self._atualizar_categorias()

    # ------------------------------------------------------------------
    # 1. Formulário de lançamento (RF07, RF08, RF09)
    # ------------------------------------------------------------------

    def _montar_formulario(self) -> None:
        caixa = ttk.LabelFrame(self, text="Lançamento", padding=10)
        caixa.pack(side="top", fill="x")

        # Tipo começa sem escolha: o usuário decide se é entrada ou saída.
        self.tipo = tk.StringVar(value="")
        ttk.Label(caixa, text="Tipo").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        tipos = ttk.Frame(caixa)
        tipos.grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(tipos, text="Saída (gasto)", variable=self.tipo, value=SAIDA).pack(side="left")
        ttk.Radiobutton(tipos, text="Entrada (recebido)", variable=self.tipo, value=ENTRADA).pack(
            side="left", padx=(12, 0)
        )

        ttk.Label(caixa, text="Data").grid(row=0, column=2, sticky="w", padx=(24, 8))
        linha_data = ttk.Frame(caixa)
        linha_data.grid(row=0, column=3, sticky="w")
        self.campo_data = ttk.Entry(linha_data, width=12)
        self.campo_data.pack(side="left")
        ttk.Button(linha_data, text="Hoje", width=6, command=self._preencher_hoje).pack(side="left", padx=(6, 0))
        ttk.Label(linha_data, text="DD/MM/AAAA", foreground="gray40").pack(side="left", padx=(8, 0))

        ttk.Label(caixa, text="Valor (R$)").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        self.campo_valor = ttk.Entry(caixa, width=16)
        self.campo_valor.grid(row=1, column=1, sticky="w")

        ttk.Label(caixa, text="Categoria").grid(row=1, column=2, sticky="w", padx=(24, 8))
        # Combobox editável: escolhe uma categoria existente ou digita uma nova (RF09).
        self.campo_categoria = ttk.Combobox(caixa, width=24)
        self.campo_categoria.grid(row=1, column=3, sticky="w")

        ttk.Label(caixa, text="Descrição").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
        self.campo_descricao = ttk.Entry(caixa)
        self.campo_descricao.grid(row=2, column=1, columnspan=3, sticky="ew")
        ttk.Label(caixa, text="opcional", foreground="gray40").grid(row=2, column=4, sticky="w", padx=(8, 0))
        caixa.columnconfigure(3, weight=1)

        botoes = ttk.Frame(caixa)
        botoes.grid(row=3, column=0, columnspan=5, sticky="w", pady=(8, 0))
        self.botao_salvar = ttk.Button(botoes, text="Adicionar", command=self.salvar_lancamento)
        self.botao_salvar.pack(side="left")
        self.botao_cancelar = ttk.Button(botoes, text="Cancelar edição", command=self._limpar_formulario)
        self.aviso_edicao = ttk.Label(botoes, foreground="#9a6700")

        for campo in (self.campo_data, self.campo_valor, self.campo_categoria, self.campo_descricao):
            campo.bind("<Return>", lambda _evento: self.salvar_lancamento())

    def _preencher_hoje(self) -> None:
        # Só acontece quando o usuário clica em "Hoje".
        self.campo_data.delete(0, "end")
        self.campo_data.insert(0, formatar_data(date.today()))

    def salvar_lancamento(self) -> None:
        """Adiciona um lançamento novo ou grava a edição em andamento."""
        try:
            lancamento = novo_lancamento(
                self.tipo.get(),
                ler_campo(self.campo_valor, ler_dinheiro, "Valor"),
                ler_campo(self.campo_data, ler_data, "Data"),
                self.campo_categoria.get(),
                self.campo_descricao.get(),
                self._editando.id if self._editando else None,
            )
            if self._editando:
                self.repo.atualizar(lancamento)
            else:
                lancamento = self.repo.adicionar(lancamento)
        except ErroDeValidacao as erro:
            mostrar_erro(self, erro)
            return

        self._limpar_formulario(manter_data=True)
        self._atualizar_categorias()
        # Mostra o mês do lançamento salvo, para o usuário vê-lo na lista.
        self._mostrar_mes(lancamento.data.year, lancamento.data.month)
        self._selecionar(lancamento.id)

    def _editar_selecionado(self) -> None:
        lancamento = self._selecionado()
        if lancamento is None:
            return
        self._limpar_formulario()
        self._editando = lancamento
        self.tipo.set(lancamento.tipo)
        self.campo_data.insert(0, formatar_data(lancamento.data))
        self.campo_valor.insert(0, formatar_numero(lancamento.valor))
        self.campo_categoria.set(lancamento.categoria)
        self.campo_descricao.insert(0, lancamento.descricao)
        self.botao_salvar.configure(text="Salvar alterações")
        self.botao_cancelar.pack(side="left", padx=(8, 0))
        self.aviso_edicao.configure(text=f"Editando o lançamento de {formatar_data(lancamento.data)}")
        self.aviso_edicao.pack(side="left", padx=(12, 0))
        self.campo_valor.focus_set()

    def _limpar_formulario(self, manter_data: bool = False) -> None:
        """Volta ao modo "novo lançamento". `manter_data` ajuda a lançar vários gastos do mesmo dia."""
        self._editando = None
        self.tipo.set("")
        if not manter_data:
            self.campo_data.delete(0, "end")
        for campo in (self.campo_valor, self.campo_descricao):
            campo.delete(0, "end")
        self.campo_categoria.set("")
        self.botao_salvar.configure(text="Adicionar")
        self.botao_cancelar.pack_forget()
        self.aviso_edicao.pack_forget()

    def _atualizar_categorias(self) -> None:
        self.campo_categoria.configure(values=self.repo.categorias())

    # ------------------------------------------------------------------
    # 2. Lista do mês (RF08 editar/excluir, RF10 filtro)
    # ------------------------------------------------------------------

    def _montar_lista(self) -> None:
        caixa = ttk.LabelFrame(self, text="Lançamentos do mês", padding=10)
        caixa.pack(side="top", fill="both", expand=True, pady=(10, 0))

        filtro = ttk.Frame(caixa)
        filtro.pack(side="top", fill="x")
        ttk.Button(filtro, text="◀", width=3, command=lambda: self._andar_mes(-1)).pack(side="left")
        self.campo_mes = ttk.Combobox(filtro, values=MESES, state="readonly", width=11)
        self.campo_mes.pack(side="left", padx=(6, 4))
        self.campo_ano = ttk.Spinbox(filtro, from_=1900, to=2999, width=6)
        self.campo_ano.pack(side="left")
        ttk.Button(filtro, text="▶", width=3, command=lambda: self._andar_mes(1)).pack(side="left", padx=(4, 0))
        ttk.Button(filtro, text="Filtrar", command=self._filtrar).pack(side="left", padx=(8, 0))
        self.campo_mes.bind("<<ComboboxSelected>>", lambda _evento: self._filtrar())
        self.campo_ano.bind("<Return>", lambda _evento: self._filtrar())

        self.totais = ttk.Label(filtro)
        self.totais.pack(side="right")

        moldura = ttk.Frame(caixa)
        moldura.pack(side="top", fill="both", expand=True, pady=(8, 0))
        self.tabela = ttk.Treeview(moldura, columns=COLUNAS, show="headings", height=8, selectmode="browse")
        for coluna, titulo, largura, ancora in [
            ("data", "Data", 95, "w"),
            ("tipo", "Tipo", 75, "w"),
            ("categoria", "Categoria", 150, "w"),
            ("descricao", "Descrição", 300, "w"),
            ("valor", "Valor", 120, "e"),
        ]:
            self.tabela.heading(coluna, text=titulo, anchor=ancora)
            self.tabela.column(coluna, width=largura, anchor=ancora, stretch=coluna == "descricao")
        self.tabela.tag_configure(SAIDA, foreground="#b42318")
        self.tabela.tag_configure(ENTRADA, foreground="#067647")
        rolagem = ttk.Scrollbar(moldura, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=rolagem.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="left", fill="y")
        self.tabela.bind("<Double-1>", lambda _evento: self._editar_selecionado())
        self.tabela.bind("<Delete>", lambda _evento: self._excluir_selecionado())

        botoes = ttk.Frame(caixa)
        botoes.pack(side="top", fill="x", pady=(8, 0))
        ttk.Button(botoes, text="Editar selecionado", command=self._editar_selecionado).pack(side="left")
        ttk.Button(botoes, text="Excluir selecionado", command=self._excluir_selecionado).pack(
            side="left", padx=(8, 0)
        )
        ttk.Label(botoes, text="Dica: duplo clique edita; Delete exclui.", foreground="gray40").pack(
            side="left", padx=(12, 0)
        )

    def _mostrar_mes(self, ano: int, mes: int) -> None:
        self.campo_mes.current(mes - 1)
        self.campo_ano.set(ano)
        self._recarregar(ano, mes)

    def _filtrar(self) -> None:
        try:
            ano = int(self.campo_ano.get())
            self._recarregar(ano, self.campo_mes.current() + 1)
        except ValueError:
            mostrar_erro(self, ErroDeValidacao("Ano: informe um ano com 4 dígitos, por exemplo 2026."))
        except ErroDeValidacao as erro:
            mostrar_erro(self, erro)

    def _andar_mes(self, passo: int) -> None:
        """Botões ◀ ▶: mês anterior ou seguinte (dezembro + 1 = janeiro do ano seguinte)."""
        try:
            ano = int(self.campo_ano.get())
        except ValueError:
            ano = date.today().year
        indice = ano * 12 + self.campo_mes.current() + passo
        self._mostrar_mes(indice // 12, indice % 12 + 1)

    def _recarregar(self, ano: int, mes: int) -> None:
        """Busca o mês no banco e redesenha a tabela e os totais."""
        inicio, fim = periodo_do_mes(ano, mes)
        lancamentos = self.repo.listar_periodo(inicio, fim)

        self.tabela.delete(*self.tabela.get_children())
        self._lancamentos = {}
        for l in lancamentos:
            linha = str(l.id)
            self._lancamentos[linha] = l
            self.tabela.insert(
                "", "end", iid=linha, tags=(l.tipo,),
                values=(
                    formatar_data(l.data),
                    "Saída" if l.eh_saida else "Entrada",
                    l.categoria,
                    l.descricao,
                    formatar_reais(l.valor),
                ),
            )

        resumo = resumir(lancamentos, inicio, fim)
        self.totais.configure(
            text=f"Entradas: {formatar_reais(resumo.total_entradas)}   "
            f"Saídas: {formatar_reais(resumo.total_saidas)}   "
            f"Saldo: {formatar_reais(resumo.saldo)}"
        )

    def _selecionado(self) -> Lancamento | None:
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Nenhum lançamento selecionado", "Clique em um lançamento da lista primeiro.", parent=self)
            return None
        return self._lancamentos[selecao[0]]

    def _selecionar(self, id_lancamento: int | None) -> None:
        linha = str(id_lancamento)
        if self.tabela.exists(linha):
            self.tabela.selection_set(linha)
            self.tabela.see(linha)

    def _excluir_selecionado(self) -> None:
        lancamento = self._selecionado()
        if lancamento is None:
            return
        tipo = "saída" if lancamento.eh_saida else "entrada"
        descricao = f" ({lancamento.descricao})" if lancamento.descricao else ""
        confirmado = messagebox.askyesno(
            "Excluir lançamento",
            f"Excluir a {tipo} de {formatar_reais(lancamento.valor)} em {formatar_data(lancamento.data)}, "
            f"categoria {lancamento.categoria}{descricao}?\n\nIsso não pode ser desfeito.",
            icon="warning",
            default="no",
            parent=self,
        )
        if not confirmado:
            return
        try:
            self.repo.excluir(lancamento.id)
        except ErroDeValidacao as erro:
            mostrar_erro(self, erro)
        if self._editando and self._editando.id == lancamento.id:
            self._limpar_formulario()
        self._atualizar_categorias()
        self._filtrar()

    # ------------------------------------------------------------------
    # 3. Relatório de gastos (RF11)
    # ------------------------------------------------------------------

    def _montar_relatorio(self) -> None:
        caixa = ttk.LabelFrame(self, text="Relatório de gastos", padding=10)
        caixa.pack(side="top", fill="x", pady=(10, 0))
        ttk.Label(caixa, text="De").pack(side="left")
        self.campo_inicio = ttk.Entry(caixa, width=12)
        self.campo_inicio.pack(side="left", padx=(6, 12))
        ttk.Label(caixa, text="Até").pack(side="left")
        self.campo_fim = ttk.Entry(caixa, width=12)
        self.campo_fim.pack(side="left", padx=(6, 8))
        ttk.Button(caixa, text="Usar o mês da lista", command=self._periodo_do_mes_filtrado).pack(side="left")
        ttk.Button(caixa, text="Gerar relatório", command=self.gerar_relatorio).pack(side="left", padx=(8, 0))
        for campo in (self.campo_inicio, self.campo_fim):
            campo.bind("<Return>", lambda _evento: self.gerar_relatorio())

    def _periodo_do_mes_filtrado(self) -> None:
        try:
            inicio, fim = periodo_do_mes(int(self.campo_ano.get()), self.campo_mes.current() + 1)
        except (ValueError, ErroDeValidacao):
            mostrar_erro(self, ErroDeValidacao("Ano: informe um ano com 4 dígitos, por exemplo 2026."))
            return
        for campo, data in ((self.campo_inicio, inicio), (self.campo_fim, fim)):
            campo.delete(0, "end")
            campo.insert(0, formatar_data(data))

    def gerar_relatorio(self) -> None:
        """Abre uma janela com o relatório do período e o botão de salvar."""
        momento = datetime.now()
        try:
            inicio = ler_campo(self.campo_inicio, ler_data, "Data inicial")
            fim = ler_campo(self.campo_fim, ler_data, "Data final")
            resumo = resumir(self.repo.listar_periodo(inicio, fim), inicio, fim)
        except ErroDeValidacao as erro:
            mostrar_erro(self, erro)
            return

        janela = tk.Toplevel(self)
        janela.title(f"Relatório de gastos: {formatar_data(inicio)} a {formatar_data(fim)}")
        janela.geometry("860x640")
        painel = PainelRelatorio(janela)
        painel.pack(fill="both", expand=True, padx=10, pady=10)
        painel.mostrar(relatorio_gastos(resumo, momento), nome_arquivo("relatorio-gastos", momento))
