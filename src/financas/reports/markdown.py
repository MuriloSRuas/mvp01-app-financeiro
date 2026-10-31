"""Relatórios em Markdown dos cálculos (RF05 e a geração do texto do RF06).

Cada relatório segue a mesma ordem, que é o princípio "sem dívida cognitiva"
do projeto: o usuário vê **o que informou, a fórmula, cada passo e o resultado**,
e não só o número final. Assim ele consegue refazer a conta no caderno.

    título · data/hora · dados informados · fórmula · passo a passo · resultado · aviso

O texto gerado aqui é o mesmo que a tela mostra e o que vai para o arquivo
`.md` (aberto no Obsidian). Este módulo só monta texto: não sabe de janela
nem de arquivo.
"""

from datetime import datetime
from decimal import Decimal

from financas.core.antecipacao import ResultadoAntecipacao, valor_presente
from financas.core.dinheiro import (
    arredondar,
    formatar_numero,
    formatar_reais,
    formatar_taxa,
)
from financas.core.meta_economia import LinhaMes, ResultadoAporte, ResultadoMeses

# Tabelas de até 24 meses aparecem inteiras; acima disso, resumidas.
MESES_TABELA_COMPLETA = 24

AVISO_META = (
    "Os valores são uma **estimativa**: consideram a taxa constante e o aporte "
    "sempre no fim do mês. A rentabilidade real pode variar; confirme as "
    "condições com o banco ou a corretora."
)

AVISO_ANTECIPACAO = (
    "Os valores são uma **estimativa** pela fórmula de valor presente. A quitação "
    "real depende do contrato e deve ser confirmada com o credor."
)


# ---------------------------------------------------------------------------
# Meta de economia
# ---------------------------------------------------------------------------


def relatorio_meses(resultado: ResultadoMeses, gerado_em: datetime | None = None) -> str:
    """Relatório do RF01: em quantos meses a meta é atingida."""
    r = resultado
    linhas = _cabecalho("Meta de economia: em quantos meses?", gerado_em)

    linhas += _secao("Dados informados")
    linhas += _tabela(
        ["Parâmetro", "Valor"],
        [
            ["Valor da meta (M)", formatar_reais(r.meta)],
            ["Aporte mensal (A)", formatar_reais(r.aporte)],
            ["Rentabilidade (i)", f"{formatar_taxa(r.taxa)} ao mês"],
        ],
    )

    linhas += _secao("Fórmula")
    if r.taxa == 0:
        linhas += _bloco_formula(["meses = M / A   (arredondado para cima)"])
        linhas.append("Sem rendimento, o saldo cresce só com os aportes.")
    else:
        linhas += _bloco_formula(["saldo do mês = saldo anterior × (1 + i) + A"])
        linhas.append(
            "Com rendimento não há uma divisão simples: o saldo é simulado mês a mês, "
            "até alcançar a meta."
        )
        linhas.append("")
        linhas.append("O aporte é feito no **fim** de cada mês, então só começa a render no mês seguinte.")

    linhas += _secao("Passo a passo")
    if r.taxa == 0:
        divisao = r.meta / r.aporte
        conta = f"M / A = {formatar_numero(r.meta)} / {formatar_numero(r.aporte)}"
        if divisao == r.meses:
            linhas.append(f"{conta} = {r.meses}")
        else:
            linhas.append(
                f"{conta} ≈ {formatar_numero(divisao)} → arredondando para cima: {r.meses} meses"
            )
    elif r.meses == 1:
        linhas.append(
            f"Já no primeiro mês o saldo ({formatar_reais(r.tabela[0].saldo)}) alcança a meta."
        )
    else:
        anterior, final = r.tabela[-2], r.tabela[-1]
        linhas.append(
            f"No mês {anterior.mes} o saldo é {formatar_reais(anterior.saldo)}, ainda abaixo da meta; "
            f"no mês {final.mes} chega a {formatar_reais(final.saldo)}."
        )
    linhas.append("")
    linhas += _tabela_mes_a_mes(r.tabela)

    saldo_final = arredondar(r.tabela[-1].saldo)
    total_aportes = r.aporte * r.meses
    linhas += _secao("Resultado")
    linhas.append(f"**{_duracao(r.meses)}**")
    linhas.append("")
    linhas.append(
        f"Guardando {formatar_reais(r.aporte)} no fim de cada mês"
        f"{_texto_rendimento(r.taxa)}, você atinge a meta de {formatar_reais(r.meta)} "
        f"no {r.meses}º mês."
    )
    linhas.append("")
    linhas += _resumo_saldo(saldo_final, total_aportes)

    linhas += _aviso(AVISO_META)
    return _juntar(linhas)


def relatorio_aporte(resultado: ResultadoAporte, gerado_em: datetime | None = None) -> str:
    """Relatório do RF02: quanto guardar por mês para atingir a meta no prazo."""
    r = resultado
    linhas = _cabecalho("Meta de economia: quanto guardar por mês?", gerado_em)

    linhas += _secao("Dados informados")
    linhas += _tabela(
        ["Parâmetro", "Valor"],
        [
            ["Valor da meta (M)", formatar_reais(r.meta)],
            ["Prazo (n)", _plural(r.prazo, "mês", "meses")],
            ["Rentabilidade (i)", f"{formatar_taxa(r.taxa)} ao mês"],
        ],
    )

    linhas += _secao("Fórmula")
    if r.taxa == 0:
        linhas += _bloco_formula(["A = M / n"])
    else:
        linhas += _bloco_formula(["A = M × i / ((1 + i)^n − 1)"])
        linhas.append(
            "É a fórmula do valor acumulado por depósitos mensais iguais, resolvida para achar o depósito."
        )
        linhas.append("")
    linhas.append(
        "O resultado é arredondado **para cima** ao centavo, para o saldo final não ficar abaixo da meta. "
        "O aporte é feito no **fim** de cada mês."
    )

    linhas += _secao("Passo a passo")
    if r.taxa == 0:
        passos = [f"A = {formatar_numero(r.meta)} / {r.prazo} = {formatar_numero(r.aporte_exato, 4)}"]
    else:
        i = formatar_numero(r.taxa, _casas_taxa(r.taxa))
        fator = (1 + r.taxa) ** r.prazo
        numerador = r.meta * r.taxa
        passos = [
            f"(1 + i)^n = (1 + {i})^{r.prazo} = {formatar_numero(fator, 6)}",
            f"(1 + i)^n − 1 = {formatar_numero(fator - 1, 6)}",
            f"M × i = {formatar_numero(r.meta)} × {i} = {formatar_numero(numerador, 4)}",
            f"A = {formatar_numero(numerador, 4)} / {formatar_numero(fator - 1, 6)}"
            f" = {formatar_numero(r.aporte_exato, 4)}",
        ]
    passos.append(f"Arredondando para cima: **{formatar_reais(r.aporte)}**")
    linhas += [f"{numero}. {passo}" for numero, passo in enumerate(passos, start=1)]
    linhas.append("")
    linhas.append(f"Simulação guardando {formatar_reais(r.aporte)} por mês:")
    linhas.append("")
    linhas += _tabela_mes_a_mes(r.tabela)

    saldo_final = arredondar(r.tabela[-1].saldo)
    total_aportes = r.aporte * r.prazo
    linhas += _secao("Resultado")
    linhas.append(f"**{formatar_reais(r.aporte)} por mês**")
    linhas.append("")
    linhas.append(
        f"Guardando {formatar_reais(r.aporte)} no fim de cada mês durante {_duracao(r.prazo)}"
        f"{_texto_rendimento(r.taxa)}, você atinge a meta de {formatar_reais(r.meta)}."
    )
    linhas.append("")
    linhas += _resumo_saldo(saldo_final, total_aportes)

    linhas += _aviso(AVISO_META)
    return _juntar(linhas)


def _tabela_mes_a_mes(tabela: tuple[LinhaMes, ...]) -> list[str]:
    exibidas = _linhas_exibidas(tabela)
    linhas = _tabela(
        ["Mês", "Aporte", "Rendimento", "Saldo"],
        [
            [str(l.mes), formatar_reais(l.aporte), formatar_reais(l.rendimento), formatar_reais(l.saldo)]
            for l in exibidas
        ],
    )
    if len(exibidas) < len(tabela):
        linhas.append("")
        linhas.append(
            f"_Tabela resumida: mostra os 12 primeiros meses, o fim de cada ano e o último mês "
            f"({len(exibidas)} de {len(tabela)} meses)._"
        )
    return linhas


def _linhas_exibidas(tabela: tuple[LinhaMes, ...]) -> list[LinhaMes]:
    """Prazos longos: início, marcos anuais e fim, como o plano permite."""
    if len(tabela) <= MESES_TABELA_COMPLETA:
        return list(tabela)
    ultimo = len(tabela)
    return [l for l in tabela if l.mes <= 12 or l.mes % 12 == 0 or l.mes == ultimo]


def _resumo_saldo(saldo_final: Decimal, total_aportes: Decimal) -> list[str]:
    # Rendimentos = saldo exibido − aportes, para a soma fechar na tela.
    return _tabela(
        ["", "Valor"],
        [
            ["Total guardado (aportes)", formatar_reais(total_aportes)],
            ["Total de rendimentos", formatar_reais(saldo_final - total_aportes)],
            ["**Saldo final**", f"**{formatar_reais(saldo_final)}**"],
        ],
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


def relatorio_antecipacao(resultado: ResultadoAntecipacao, gerado_em: datetime | None = None) -> str:
    """Relatório do RF03 (quantidade informada) ou do RF04 (valor disponível)."""
    r = resultado
    por_valor = r.valor_disponivel is not None
    linhas = _cabecalho("Antecipação de parcelas", gerado_em)

    linhas += _secao("Dados informados")
    parametros = [
        ["Valor da parcela (P)", formatar_reais(r.valor_parcela)],
        ["Juros do contrato (i)", f"{formatar_taxa(r.taxa)} ao mês"],
        ["Parcelas restantes, além da atual (m)", str(r.parcelas_restantes)],
    ]
    if por_valor:
        parametros.append(["Valor disponível para antecipar", formatar_reais(r.valor_disponivel)])
    else:
        parametros.append(["Parcelas a antecipar", str(r.quantidade)])
    linhas += _tabela(["Parâmetro", "Valor"], parametros)

    linhas += _secao("Fórmula")
    linhas += _bloco_formula(["valor a pagar hoje = P / (1 + i)^j", "economia = P − valor a pagar hoje"])
    linhas.append(
        "`j` é o número de meses até o vencimento da parcela. Pagando hoje, você deixa de pagar "
        "os juros desses `j` meses. As **últimas** parcelas (maior `j`) são antecipadas primeiro, "
        "porque são as que mais economizam."
    )
    if por_valor:
        linhas.append("")
        linhas.append(
            "Com valor disponível: soma-se o valor a pagar a partir da última parcela, indo para trás, "
            "enquanto o total couber no valor."
        )

    linhas += _secao("Passo a passo")
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
        corpo.append(["**Total**", "", f"**{formatar_reais(r.total_a_pagar)}**", f"**{formatar_reais(r.total_economia)}**"])
        linhas += _tabela(["Vence em", "Cálculo", "Valor a pagar hoje", "Economia"], corpo)
    else:
        linhas.append("Nenhuma parcela antecipada.")
    if por_valor:
        linhas.append("")
        linhas += _motivo_parada(r)

    linhas += _secao("Resultado")
    linhas += _resultado_antecipacao(r)

    linhas += _aviso(AVISO_ANTECIPACAO)
    return _juntar(linhas)


def _motivo_parada(r: ResultadoAntecipacao) -> list[str]:
    """RF04: explica por que parou (a próxima parcela não cabe, ou acabaram)."""
    proxima = r.parcelas_restantes - r.quantidade
    if proxima == 0:
        return ["Todas as parcelas restantes couberam no valor disponível."]
    custo = arredondar(valor_presente(r.valor_parcela, r.taxa, proxima))
    return [
        f"A próxima parcela (vence em {_plural(proxima, 'mês', 'meses')}) custaria "
        f"{formatar_reais(custo)} hoje e não cabe no que sobra ({formatar_reais(r.sobra)})."
    ]


def _resultado_antecipacao(r: ResultadoAntecipacao) -> list[str]:
    linhas = []
    if r.quantidade == 0:
        linhas.append("**Nenhuma parcela antecipada.**")
    else:
        linhas.append(
            f"**Pagando {formatar_reais(r.total_a_pagar)} hoje, você economiza "
            f"{formatar_reais(r.total_economia)} em juros.**"
        )
        linhas.append("")
        if r.quantidade == 1:
            quitadas = f"a parcela que venceria em {_plural(r.linhas[0].vence_em_meses, 'mês', 'meses')}"
        else:
            vencimentos = _lista_pt([str(l.vence_em_meses) for l in r.linhas])
            quitadas = f"{r.quantidade} parcelas (as que venceriam em {vencimentos} meses)"
        linhas.append(
            f"Isso quita {quitadas}, no lugar de pagar "
            f"{formatar_reais(r.valor_parcela * r.quantidade)} nas datas originais."
        )

    linhas.append("")
    linhas.append(f"Continuam a vencer normalmente: {_parcelas_que_ficam(r)}.")
    if r.sobra is not None:
        linhas.append("")
        linhas.append(f"Sobram {formatar_reais(r.sobra)} do valor disponível.")
    return linhas


def _parcelas_que_ficam(r: ResultadoAntecipacao) -> str:
    restantes = r.parcelas_restantes - r.quantidade
    if restantes == 0:
        return "só a parcela atual (paga hoje); não resta nenhuma outra"
    if restantes == 1:
        return "a parcela atual (paga hoje) e a que vence em 1 mês"
    return f"a parcela atual (paga hoje) e as {restantes} que vencem de 1 a {restantes} meses"


# ---------------------------------------------------------------------------
# Peças de Markdown
# ---------------------------------------------------------------------------


def _cabecalho(titulo: str, gerado_em: datetime | None) -> list[str]:
    momento = gerado_em or datetime.now()
    return [f"# {titulo}", "", f"Gerado em {momento:%d/%m/%Y} às {momento:%H:%M}."]


def _secao(titulo: str) -> list[str]:
    return ["", f"## {titulo}", ""]


def _tabela(cabecalhos: list[str], corpo: list[list[str]]) -> list[str]:
    """Tabela Markdown com colunas alinhadas por espaços.

    O alinhamento não muda nada no Obsidian (ele ignora os espaços extras),
    mas deixa a tabela legível na tela do programa, que mostra o texto puro.
    """
    larguras = [
        max(3, len(cabecalho), *(len(celulas[coluna]) for celulas in corpo))
        for coluna, cabecalho in enumerate(cabecalhos)
    ]

    def linha(celulas: list[str]) -> str:
        return "| " + " | ".join(c.ljust(l) for c, l in zip(celulas, larguras)) + " |"

    separador = "| " + " | ".join("-" * l for l in larguras) + " |"
    return [linha(cabecalhos), separador, *(linha(celulas) for celulas in corpo)]


def _bloco_formula(formulas: list[str]) -> list[str]:
    return ["```text", *formulas, "```", ""]


def _aviso(texto: str) -> list[str]:
    # "> [!warning]" vira um quadro de alerta no Obsidian; em outros leitores
    # de Markdown aparece como uma citação comum, que também funciona.
    return ["", "> [!warning] Aviso", f"> {texto}"]


def _juntar(linhas: list[str]) -> str:
    return "\n".join(linhas) + "\n"


def _plural(quantidade: int, singular: str, plural: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else plural}"


def _duracao(meses: int) -> str:
    """50 -> "50 meses (4 anos e 2 meses)"; 12 -> "12 meses (1 ano)"; 5 -> "5 meses"."""
    texto = _plural(meses, "mês", "meses")
    anos, resto = divmod(meses, 12)
    if anos == 0:
        return texto
    partes = _plural(anos, "ano", "anos")
    if resto:
        partes += " e " + _plural(resto, "mês", "meses")
    return f"{texto} ({partes})"


def _lista_pt(itens: list[str]) -> str:
    """["10", "9", "8"] -> "10, 9 e 8". Recebe pelo menos dois itens."""
    return ", ".join(itens[:-1]) + " e " + itens[-1]
