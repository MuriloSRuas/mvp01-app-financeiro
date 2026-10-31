"""Meta de economia (cofrinho).

Duas perguntas, uma para cada requisito:

- RF01: "guardando A por mês, em quantos meses chego à meta M?" -> `calcular_meses`
- RF02: "para chegar à meta M em n meses, quanto guardo por mês?" -> `calcular_aporte`

Premissa: o aporte é feito no **fim** de cada mês. Então o rendimento de um mês
incide sobre o saldo do mês anterior, e o aporte daquele mês só rende no
seguinte. A taxa `taxa` é a fração ao mês (0,5% a.m. = Decimal("0.005")).

As contas guardam precisão total; quem mostra os valores (relatório) arredonda.
"""

import math
from dataclasses import dataclass
from decimal import Decimal

from financas.core.dinheiro import (
    ErroDeValidacao,
    arredondar_para_cima,
    exigir_inteiro,
    exigir_nao_negativo,
    exigir_positivo,
    formatar_reais,
)

# Limite de segurança: 100 anos. Evita laço infinito (taxa alta demais não é o
# problema; aporte pequeno demais é) e tabelas gigantes que travariam a tela.
# Decidido com o usuário: vale com e sem juros, e também para o prazo do RF02.
LIMITE_MESES = 1200


class MetaInalcancavel(ErroDeValidacao):
    """A meta não é atingida dentro de LIMITE_MESES com os dados informados."""


@dataclass(frozen=True)
class LinhaMes:
    """Uma linha da tabela mês a mês do relatório."""

    mes: int
    aporte: Decimal
    rendimento: Decimal
    saldo: Decimal


@dataclass(frozen=True)
class ResultadoMeses:
    """Resposta do RF01: em quantos meses a meta é atingida."""

    meta: Decimal
    aporte: Decimal
    taxa: Decimal
    meses: int
    tabela: tuple[LinhaMes, ...]


@dataclass(frozen=True)
class ResultadoAporte:
    """Resposta do RF02: quanto guardar por mês.

    `aporte_exato` é o valor da fórmula, antes de arredondar; o relatório o
    mostra no passo a passo. `aporte` é o valor arredondado para o centavo de
    cima, que é o que o usuário de fato vai guardar (e que gera a `tabela`).
    """

    meta: Decimal
    prazo: int
    taxa: Decimal
    aporte_exato: Decimal
    aporte: Decimal
    tabela: tuple[LinhaMes, ...]


def calcular_meses(meta: Decimal, aporte: Decimal, taxa: Decimal = Decimal(0)) -> ResultadoMeses:
    """RF01: quantos meses, guardando `aporte` por mês, até o saldo alcançar `meta`.

    Sem juros a resposta sai direto da divisão: ceil(M / A), arredondando o
    número de meses para cima (49,5 meses = 50 meses para completar a meta).
    Com juros não há uma conta simples e legível, então simulamos mês a mês,
    exatamente como se faria no caderno, até o saldo passar da meta.
    """
    exigir_positivo(meta, "Valor da meta")
    exigir_positivo(aporte, "Aporte mensal")
    exigir_nao_negativo(taxa, "Taxa de rentabilidade")

    if taxa == 0:
        meses = math.ceil(meta / aporte)
        if meses > LIMITE_MESES:
            raise _meta_inalcancavel(meta, aporte)
        return ResultadoMeses(meta, aporte, taxa, meses, simular(aporte, taxa, meses))

    linhas = []
    saldo = Decimal(0)
    for mes in range(1, LIMITE_MESES + 1):
        linha = _proximo_mes(mes, saldo, aporte, taxa)
        linhas.append(linha)
        saldo = linha.saldo
        if saldo >= meta:
            return ResultadoMeses(meta, aporte, taxa, mes, tuple(linhas))
    raise _meta_inalcancavel(meta, aporte)


def calcular_aporte(meta: Decimal, prazo: int, taxa: Decimal = Decimal(0)) -> ResultadoAporte:
    """RF02: aporte mensal necessário para atingir `meta` em `prazo` meses.

    - Sem juros: A = M / n.
    - Com juros: A = M * i / ((1 + i)^n - 1). É a fórmula do valor futuro de
      uma série de depósitos iguais, "invertida" para achar o depósito.

    Nos dois casos o resultado é arredondado para o centavo de cima, para que
    o saldo final nunca fique abaixo da meta.
    """
    exigir_positivo(meta, "Valor da meta")
    exigir_inteiro(prazo, "Prazo em meses", minimo=1, maximo=LIMITE_MESES)
    exigir_nao_negativo(taxa, "Taxa de rentabilidade")

    if taxa == 0:
        aporte_exato = meta / prazo
    else:
        aporte_exato = meta * taxa / ((1 + taxa) ** prazo - 1)

    aporte = arredondar_para_cima(aporte_exato)
    return ResultadoAporte(meta, prazo, taxa, aporte_exato, aporte, simular(aporte, taxa, prazo))


def simular(aporte: Decimal, taxa: Decimal, meses: int) -> tuple[LinhaMes, ...]:
    """Monta a tabela mês a mês: a cada mês o saldo rende e recebe o aporte."""
    linhas = []
    saldo = Decimal(0)
    for mes in range(1, meses + 1):
        linha = _proximo_mes(mes, saldo, aporte, taxa)
        linhas.append(linha)
        saldo = linha.saldo
    return tuple(linhas)


def _proximo_mes(mes: int, saldo_anterior: Decimal, aporte: Decimal, taxa: Decimal) -> LinhaMes:
    # saldo = saldo * (1 + i) + A, separado em partes para a tabela mostrar o rendimento.
    rendimento = saldo_anterior * taxa
    return LinhaMes(mes, aporte, rendimento, saldo_anterior + rendimento + aporte)


def _meta_inalcancavel(meta: Decimal, aporte: Decimal) -> MetaInalcancavel:
    return MetaInalcancavel(
        f"Guardando {formatar_reais(aporte)} por mês, a meta de {formatar_reais(meta)} "
        f"não é atingida em {LIMITE_MESES} meses ({LIMITE_MESES // 12} anos). "
        "Aumente o aporte ou revise a meta."
    )
