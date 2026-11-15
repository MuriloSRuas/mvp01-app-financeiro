"""Relatórios dos cálculos e dos gastos (RF05, RF11).

Cada relatório segue a mesma ordem, que é o princípio "sem dívida cognitiva"
do projeto: o usuário vê **o que informou, a fórmula, cada passo e o resultado**,
e não só o número final. Assim ele consegue refazer a conta no caderno.

    título · data/hora · dados informados · fórmula · passo a passo · resultado · aviso

As funções devolvem um `Documento` (ver `documento.py`): a tela o desenha
formatado e, se o usuário quiser, `markdown.py` o converte para salvar em
arquivo. Este módulo só monta o conteúdo: não sabe de janela nem de arquivo.
"""

from datetime import datetime
from decimal import Decimal

from financas.core.antecipacao import ResultadoAntecipacao, valor_presente
from financas.core.dinheiro import (
    arredondar,
    formatar_numero,
    formatar_percentual,
    formatar_reais,
    formatar_taxa,
)
from financas.core.gastos import ResumoPeriodo, formatar_data
from financas.core.meta_economia import LinhaMes, ResultadoAporte, ResultadoMeses
from financas.reports.documento import Documento, Texto, codigo, italico, negrito, texto

# Tabelas de até 24 meses aparecem inteiras; acima disso, resumidas.
MESES_TABELA_COMPLETA = 24

AVISO_META = (
    "Os valores são uma ",
    negrito("estimativa"),
    ": consideram a taxa constante e o aporte sempre no fim do mês. A rentabilidade "
    "real pode variar; confirme as condições com o banco ou a corretora.",
)

AVISO_ANTECIPACAO = (
    "Os valores são uma ",
    negrito("estimativa"),
    " pela fórmula de valor presente. A quitação real depende do contrato e deve "
    "ser confirmada com o credor.",
)


# ---------------------------------------------------------------------------
# Meta de economia
# ---------------------------------------------------------------------------


def relatorio_meses(resultado: ResultadoMeses, gerado_em: datetime | None = None) -> Documento:
    """Relatório do RF01: em quantos meses a meta é atingida."""
    r = resultado
    doc = _novo("Meta de economia: em quantos meses?", gerado_em)

    doc.secao("Dados informados")
    doc.tabela(
        ["Parâmetro", "Valor"],
        [
            ["Valor da meta (M)", formatar_reais(r.meta)],
            ["Aporte mensal (A)", formatar_reais(r.aporte)],
            ["Rentabilidade (i)", f"{formatar_taxa(r.taxa)} ao mês"],
        ],
    )

    doc.secao("Fórmula")
    if r.taxa == 0:
        doc.formula("meses = M / A   (arredondado para cima)")
        doc.paragrafo("Sem rendimento, o saldo cresce só com os aportes.")
    else:
        doc.formula("saldo do mês = saldo anterior × (1 + i) + A")
        doc.paragrafo(
            "Com rendimento não há uma divisão simples: o saldo é simulado mês a mês, "
            "até alcançar a meta."
        )
        doc.paragrafo(
            "O aporte é feito no ", negrito("fim"), " de cada mês, então só começa a render no mês seguinte."
        )

    doc.secao("Passo a passo")
    if r.taxa == 0:
        divisao = r.meta / r.aporte
        conta = f"M / A = {formatar_numero(r.meta)} / {formatar_numero(r.aporte)}"
        if divisao == r.meses:
            doc.paragrafo(f"{conta} = {r.meses}")
        else:
            doc.paragrafo(
                f"{conta} ≈ {formatar_numero(divisao)} → arredondando para cima: {r.meses} meses"
            )
    elif r.meses == 1:
        doc.paragrafo(
            f"Já no primeiro mês o saldo ({formatar_reais(r.tabela[0].saldo)}) alcança a meta."
        )
    else:
        anterior, final = r.tabela[-2], r.tabela[-1]
        doc.paragrafo(
            f"No mês {anterior.mes} o saldo é {formatar_reais(anterior.saldo)}, ainda abaixo da meta; "
            f"no mês {final.mes} chega a {formatar_reais(final.saldo)}."
        )
    _tabela_mes_a_mes(doc, r.tabela)

    saldo_final = arredondar(r.tabela[-1].saldo)
    total_aportes = r.aporte * r.meses
    doc.secao("Resultado")
    doc.paragrafo(negrito(_duracao(r.meses)))
    doc.paragrafo(
        f"Guardando {formatar_reais(r.aporte)} no fim de cada mês"
        f"{_texto_rendimento(r.taxa)}, você atinge a meta de {formatar_reais(r.meta)} "
        f"no {r.meses}º mês."
    )
    _resumo_saldo(doc, saldo_final, total_aportes)

    doc.aviso(*AVISO_META)
    return doc


def relatorio_aporte(resultado: ResultadoAporte, gerado_em: datetime | None = None) -> Documento:
    """Relatório do RF02: quanto guardar por mês para atingir a meta no prazo."""
    r = resultado
    doc = _novo("Meta de economia: quanto guardar por mês?", gerado_em)

    doc.secao("Dados informados")
    doc.tabela(
        ["Parâmetro", "Valor"],
        [
            ["Valor da meta (M)", formatar_reais(r.meta)],
            ["Prazo (n)", _plural(r.prazo, "mês", "meses")],
            ["Rentabilidade (i)", f"{formatar_taxa(r.taxa)} ao mês"],
        ],
    )

    doc.secao("Fórmula")
    if r.taxa == 0:
        doc.formula("A = M / n")
    else:
        doc.formula("A = M × i / ((1 + i)^n − 1)")
        doc.paragrafo(
            "É a fórmula do valor acumulado por depósitos mensais iguais, resolvida para achar o depósito."
        )
    doc.paragrafo(
        "O resultado é arredondado ", negrito("para cima"), " ao centavo, para o saldo final não "
        "ficar abaixo da meta. O aporte é feito no ", negrito("fim"), " de cada mês."
    )

    doc.secao("Passo a passo")
    if r.taxa == 0:
        passos = [texto(f"A = {formatar_numero(r.meta)} / {r.prazo} = {formatar_numero(r.aporte_exato, 4)}")]
    else:
        i = formatar_numero(r.taxa, _casas_taxa(r.taxa))
        fator = (1 + r.taxa) ** r.prazo
        numerador = r.meta * r.taxa
        passos = [
            texto(f"(1 + i)^n = (1 + {i})^{r.prazo} = {formatar_numero(fator, 6)}"),
            texto(f"(1 + i)^n − 1 = {formatar_numero(fator - 1, 6)}"),
            texto(f"M × i = {formatar_numero(r.meta)} × {i} = {formatar_numero(numerador, 4)}"),
            texto(
                f"A = {formatar_numero(numerador, 4)} / {formatar_numero(fator - 1, 6)}"
                f" = {formatar_numero(r.aporte_exato, 4)}"
            ),
        ]
    passos.append(texto("Arredondando para cima: ", negrito(formatar_reais(r.aporte))))
    doc.passos(passos)
    doc.paragrafo(f"Simulação guardando {formatar_reais(r.aporte)} por mês:")
    _tabela_mes_a_mes(doc, r.tabela)

    saldo_final = arredondar(r.tabela[-1].saldo)
    total_aportes = r.aporte * r.prazo
    doc.secao("Resultado")
    doc.paragrafo(negrito(f"{formatar_reais(r.aporte)} por mês"))
    doc.paragrafo(
        f"Guardando {formatar_reais(r.aporte)} no fim de cada mês durante {_duracao(r.prazo)}"
        f"{_texto_rendimento(r.taxa)}, você atinge a meta de {formatar_reais(r.meta)}."
    )
    _resumo_saldo(doc, saldo_final, total_aportes)

    doc.aviso(*AVISO_META)
    return doc


def _tabela_mes_a_mes(doc: Documento, tabela: tuple[LinhaMes, ...]) -> None:
    exibidas = _linhas_exibidas(tabela)
    doc.tabela(
        ["Mês", "Aporte", "Rendimento", "Saldo"],
        [
            [str(l.mes), formatar_reais(l.aporte), formatar_reais(l.rendimento), formatar_reais(l.saldo)]
            for l in exibidas
        ],
    )
    if len(exibidas) < len(tabela):
        doc.paragrafo(
            italico(
                f"Tabela resumida: mostra os 12 primeiros meses, o fim de cada ano e o último mês "
                f"({len(exibidas)} de {len(tabela)} meses)."
            )
        )


def _linhas_exibidas(tabela: tuple[LinhaMes, ...]) -> list[LinhaMes]:
    """Prazos longos: início, marcos anuais e fim, como o plano permite."""
    if len(tabela) <= MESES_TABELA_COMPLETA:
        return list(tabela)
    ultimo = len(tabela)
    return [l for l in tabela if l.mes <= 12 or l.mes % 12 == 0 or l.mes == ultimo]


def _resumo_saldo(doc: Documento, saldo_final: Decimal, total_aportes: Decimal) -> None:
    # Rendimentos = saldo exibido − aportes, para a soma fechar na tela.
    doc.tabela(
        ["", "Valor"],
        [
            ["Total guardado (aportes)", formatar_reais(total_aportes)],
            ["Total de rendimentos", formatar_reais(saldo_final - total_aportes)],
            ["Saldo final", formatar_reais(saldo_final)],
        ],
        destacar_ultima=True,
    )


def _texto_rendimento(taxa: Decimal) -> str:
    if taxa == 0:
        return ", sem rendimento"
    return f", com rendimento de {formatar_taxa(taxa)} ao mês"


def _casas_taxa(taxa: Decimal) -> int:
    return max(2, -taxa.normalize().as_tuple().exponent)


# ---------------------------------------------------------------------------
# Antecipação de parcelas
# ---------------------------------------------------------------------------


def relatorio_antecipacao(resultado: ResultadoAntecipacao, gerado_em: datetime | None = None) -> Documento:
    """Relatório do RF03 (quantidade informada) ou do RF04 (valor disponível)."""
    r = resultado
    por_valor = r.valor_disponivel is not None
    doc = _novo("Antecipação de parcelas", gerado_em)

    doc.secao("Dados informados")
    parametros = [
        ["Valor da parcela (P)", formatar_reais(r.valor_parcela)],
        ["Juros do contrato (i)", f"{formatar_taxa(r.taxa)} ao mês"],
        ["Parcelas restantes, além da atual (m)", str(r.parcelas_restantes)],
    ]
    if por_valor:
        parametros.append(["Valor disponível para antecipar", formatar_reais(r.valor_disponivel)])
    else:
        parametros.append(["Parcelas a antecipar", str(r.quantidade)])
    doc.tabela(["Parâmetro", "Valor"], parametros)

    doc.secao("Fórmula")
    doc.formula("valor a pagar hoje = P / (1 + i)^j", "economia = P − valor a pagar hoje")
    doc.paragrafo(
        codigo("j"), " é o número de meses até o vencimento da parcela. Pagando hoje, você deixa de pagar "
        "os juros desses ", codigo("j"), " meses. As ", negrito("últimas"), " parcelas (maior ", codigo("j"),
        ") são antecipadas primeiro, porque são as que mais economizam.",
    )
    if por_valor:
        doc.paragrafo(
            "Com valor disponível: soma-se o valor a pagar a partir da última parcela, indo para trás, "
            "enquanto o total couber no valor."
        )

    doc.secao("Passo a passo")
    if r.linhas:
        base = formatar_numero(1 + r.taxa, _casas_taxa(r.taxa))
        corpo = [
            [
                _plural(l.vence_em_meses, "mês", "meses"),
                f"{formatar_numero(l.valor_parcela)} / {base}^{l.vence_em_meses}",
                formatar_reais(l.valor_presente),
                formatar_reais(l.economia),
            ]
            for l in r.linhas
        ]
        corpo.append(["Total", "", formatar_reais(r.total_a_pagar), formatar_reais(r.total_economia)])
        doc.tabela(["Vence em", "Cálculo", "Valor a pagar hoje", "Economia"], corpo, destacar_ultima=True)
    else:
        doc.paragrafo("Nenhuma parcela antecipada.")
    if por_valor:
        doc.paragrafo(_motivo_parada(r))

    doc.secao("Resultado")
    _resultado_antecipacao(doc, r)

    doc.aviso(*AVISO_ANTECIPACAO)
    return doc


def _motivo_parada(r: ResultadoAntecipacao) -> str:
    """RF04: explica por que parou (a próxima parcela não cabe, ou acabaram)."""
    proxima = r.parcelas_restantes - r.quantidade
    if proxima == 0:
        return "Todas as parcelas restantes couberam no valor disponível."
    custo = arredondar(valor_presente(r.valor_parcela, r.taxa, proxima))
    return (
        f"A próxima parcela (vence em {_plural(proxima, 'mês', 'meses')}) custaria "
        f"{formatar_reais(custo)} hoje e não cabe no que sobra ({formatar_reais(r.sobra)})."
    )


def _resultado_antecipacao(doc: Documento, r: ResultadoAntecipacao) -> None:
    if r.quantidade == 0:
        doc.paragrafo(negrito("Nenhuma parcela antecipada."))
    else:
        doc.paragrafo(
            negrito(
                f"Pagando {formatar_reais(r.total_a_pagar)} hoje, você economiza "
                f"{formatar_reais(r.total_economia)} em juros."
            )
        )
        if r.quantidade == 1:
            quitadas = f"a parcela que venceria em {_plural(r.linhas[0].vence_em_meses, 'mês', 'meses')}"
        else:
            vencimentos = _lista_pt([str(l.vence_em_meses) for l in r.linhas])
            quitadas = f"{r.quantidade} parcelas (as que venceriam em {vencimentos} meses)"
        doc.paragrafo(
            f"Isso quita {quitadas}, no lugar de pagar "
            f"{formatar_reais(r.valor_parcela * r.quantidade)} nas datas originais."
        )

    doc.paragrafo(f"Continuam a vencer normalmente: {_parcelas_que_ficam(r)}.")
    if r.sobra is not None:
        doc.paragrafo(f"Sobram {formatar_reais(r.sobra)} do valor disponível.")


def _parcelas_que_ficam(r: ResultadoAntecipacao) -> str:
    restantes = r.parcelas_restantes - r.quantidade
    if restantes == 0:
        return "só a parcela atual (paga hoje); não resta nenhuma outra"
    if restantes == 1:
        return "a parcela atual (paga hoje) e a que vence em 1 mês"
    return f"a parcela atual (paga hoje) e as {restantes} que vencem de 1 a {restantes} meses"


# ---------------------------------------------------------------------------
# Gastos
# ---------------------------------------------------------------------------


def relatorio_gastos(resumo: ResumoPeriodo, gerado_em: datetime | None = None) -> Documento:
    """Relatório do RF11: totais, saldo e ranking de saídas por categoria.

    Não tem aviso de estimativa: aqui não há previsão, só a soma do que foi
    lançado. Em compensação, lista os lançamentos do período, que são os
    "dados informados" deste relatório.
    """
    r = resumo
    doc = _novo("Relatório de gastos", gerado_em)
    doc.paragrafo(negrito("Período:"), f" {formatar_data(r.inicio)} a {formatar_data(r.fim)}")

    doc.secao(f"Lançamentos do período ({len(r.lancamentos)})")
    if r.lancamentos:
        doc.tabela(
            ["Data", "Tipo", "Categoria", "Descrição", "Valor"],
            [
                [
                    formatar_data(l.data),
                    "Saída" if l.eh_saida else "Entrada",
                    l.categoria,
                    l.descricao,
                    formatar_reais(l.valor),
                ]
                for l in r.lancamentos
            ],
        )
    else:
        doc.paragrafo("Nenhum lançamento no período.")

    doc.secao("Fórmulas")
    doc.formula(
        "saldo = total de entradas − total de saídas",
        "percentual da categoria = saídas da categoria / total de saídas",
    )
    doc.paragrafo(
        "O ranking considera ", negrito("apenas saídas"), ", da categoria com mais gastos para a com menos."
    )

    doc.secao("Totais")
    doc.tabela(
        ["", "Valor"],
        [
            ["Total de entradas", formatar_reais(r.total_entradas)],
            ["Total de saídas", formatar_reais(r.total_saidas)],
            ["Saldo", formatar_reais(r.saldo)],
        ],
        destacar_ultima=True,
    )
    doc.paragrafo(
        f"Saldo = {formatar_numero(r.total_entradas)} − {formatar_numero(r.total_saidas)}"
        f" = {formatar_numero(r.saldo)}"
    )

    doc.secao("Saídas por categoria")
    if r.ranking:
        doc.tabela(
            ["#", "Categoria", "Valor", "% das saídas"],
            [
                [
                    str(posicao),
                    item.categoria,
                    formatar_reais(item.valor),
                    formatar_percentual(item.percentual, 1),
                ]
                for posicao, item in enumerate(r.ranking, start=1)
            ],
        )
        primeiro = r.ranking[0]
        doc.paragrafo(
            f"Exemplo: {primeiro.categoria} = {formatar_numero(primeiro.valor)} / "
            f"{formatar_numero(r.total_saidas)} = {formatar_percentual(primeiro.percentual, 1)}"
        )
        if len(r.ranking) > 1:
            doc.paragrafo(
                italico("Os percentuais são arredondados a uma casa; por isso a soma pode dar 99,9% ou 100,1%.")
            )
    else:
        doc.paragrafo("Sem saídas no período.")

    doc.secao("Resultado")
    _resultado_gastos(doc, r)
    return doc


def _resultado_gastos(doc: Documento, r: ResumoPeriodo) -> None:
    if not r.lancamentos:
        doc.paragrafo(negrito("Nenhum lançamento no período."))
        return
    if r.saldo > 0:
        situacao: Texto = texto("saldo ", negrito(f"positivo de {formatar_reais(r.saldo)}"))
    elif r.saldo < 0:
        situacao = texto(
            "saldo ", negrito(f"negativo de {formatar_reais(-r.saldo)}"), ": você gastou mais do que recebeu"
        )
    else:
        situacao = texto("saldo ", negrito("zero"), ": você gastou exatamente o que recebeu")
    doc.paragrafo(
        f"No período, você recebeu {formatar_reais(r.total_entradas)} e gastou "
        f"{formatar_reais(r.total_saidas)}; ",
        *situacao,
        ".",
    )
    if r.ranking:
        primeiro = r.ranking[0]
        doc.paragrafo(
            "A categoria com mais gastos foi ", negrito(primeiro.categoria), ": "
            f"{formatar_reais(primeiro.valor)} ({formatar_percentual(primeiro.percentual, 1)} das saídas)."
        )


# ---------------------------------------------------------------------------
# Peças comuns
# ---------------------------------------------------------------------------


def _novo(titulo: str, gerado_em: datetime | None) -> Documento:
    return Documento(titulo, gerado_em or datetime.now())


def _plural(quantidade: int, singular: str, plural: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else plural}"


def _duracao(meses: int) -> str:
    """50 -> "50 meses (4 anos e 2 meses)"; 12 -> "12 meses (1 ano)"; 5 -> "5 meses"."""
    texto_meses = _plural(meses, "mês", "meses")
    anos, resto = divmod(meses, 12)
    if anos == 0:
        return texto_meses
    partes = _plural(anos, "ano", "anos")
    if resto:
        partes += " e " + _plural(resto, "mês", "meses")
    return f"{texto_meses} ({partes})"


def _lista_pt(itens: list[str]) -> str:
    """["10", "9", "8"] -> "10, 9 e 8". Recebe pelo menos dois itens."""
    return ", ".join(itens[:-1]) + " e " + itens[-1]
