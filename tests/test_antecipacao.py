from decimal import Decimal

import pytest

from financas.core.antecipacao import (
    antecipar_com_valor,
    antecipar_quantidade,
    valor_presente,
)
from financas.core.dinheiro import ErroDeValidacao, arredondar

PARCELA = Decimal("500.00")
DOIS_POR_CENTO = Decimal("0.02")

# --- Exemplo oficial do plano (seção 6.2) ------------------------------------


def test_exemplo_6_2_parcela_que_vence_em_10_meses():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=10, quantidade=1)
    linha = resultado.linhas[0]
    assert linha.vence_em_meses == 10
    assert linha.valor_presente == Decimal("410.17")
    assert linha.economia == Decimal("89.83")


def test_exemplo_6_2_parcela_que_vence_em_1_mes():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=1, quantidade=1)
    linha = resultado.linhas[0]
    assert linha.valor_presente == Decimal("490.20")
    assert linha.economia == Decimal("9.80")


def test_valor_presente_mantem_precisao_total():
    vp = valor_presente(PARCELA, DOIS_POR_CENTO, 10)
    assert vp != arredondar(vp)
    assert arredondar(vp) == Decimal("410.17")


# --- RF03: quantidade --------------------------------------------------------


def test_antecipa_as_ultimas_parcelas_da_ultima_para_tras():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=10, quantidade=3)
    assert [linha.vence_em_meses for linha in resultado.linhas] == [10, 9, 8]
    assert resultado.quantidade == 3


def test_cada_linha_fecha():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=24, quantidade=24)
    for linha in resultado.linhas:
        assert linha.valor_presente + linha.economia == PARCELA


def test_total_economizado_e_soma_das_linhas_arredondadas():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=10, quantidade=3)
    soma_linhas = sum(linha.economia for linha in resultado.linhas)
    assert resultado.total_economia == soma_linhas
    assert resultado.total_a_pagar == sum(linha.valor_presente for linha in resultado.linhas)
    assert resultado.total_a_pagar + resultado.total_economia == 3 * PARCELA


def test_quantidade_zero_nao_antecipa_nada():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=10, quantidade=0)
    assert resultado.linhas == ()
    assert resultado.total_a_pagar == 0
    assert resultado.total_economia == 0
    assert resultado.sobra is None


def test_quantidade_igual_as_restantes_antecipa_todas():
    resultado = antecipar_quantidade(PARCELA, DOIS_POR_CENTO, parcelas_restantes=5, quantidade=5)
    assert [linha.vence_em_meses for linha in resultado.linhas] == [5, 4, 3, 2, 1]


def test_taxa_zero_nao_tem_economia():
    resultado = antecipar_quantidade(PARCELA, Decimal(0), parcelas_restantes=5, quantidade=5)
    assert resultado.total_economia == 0
    assert resultado.total_a_pagar == 5 * PARCELA


# --- RF04: valor disponível ---------------------------------------------------


def test_valor_disponivel_paga_as_ultimas_que_cabem():
    # VP(10) = 410,17; VP(9) = 418,38; VP(8) = 426,75
    resultado = antecipar_com_valor(PARCELA, DOIS_POR_CENTO, 10, Decimal("1000.00"))
    assert [linha.vence_em_meses for linha in resultado.linhas] == [10, 9]
    assert resultado.total_a_pagar == Decimal("828.55")
    assert resultado.sobra == Decimal("171.45")


def test_valor_disponivel_exato_inclui_a_parcela():
    resultado = antecipar_com_valor(PARCELA, DOIS_POR_CENTO, 10, Decimal("828.55"))
    assert resultado.quantidade == 2
    assert resultado.sobra == 0


def test_valor_insuficiente_para_uma_parcela():
    resultado = antecipar_com_valor(PARCELA, DOIS_POR_CENTO, 10, Decimal("100.00"))
    assert resultado.linhas == ()
    assert resultado.sobra == Decimal("100.00")


def test_valor_que_sobra_paga_todas():
    resultado = antecipar_com_valor(PARCELA, DOIS_POR_CENTO, 3, Decimal("5000.00"))
    assert [linha.vence_em_meses for linha in resultado.linhas] == [3, 2, 1]
    assert resultado.sobra == Decimal("5000.00") - resultado.total_a_pagar


def test_sem_parcelas_restantes():
    resultado = antecipar_com_valor(PARCELA, DOIS_POR_CENTO, 0, Decimal("1000.00"))
    assert resultado.linhas == ()


# --- Entradas inválidas -------------------------------------------------------


@pytest.mark.parametrize("parcela", [Decimal(0), Decimal(-1)])
def test_parcela_precisa_ser_positiva(parcela):
    with pytest.raises(ErroDeValidacao, match="Valor da parcela"):
        antecipar_quantidade(parcela, DOIS_POR_CENTO, 10, 1)


def test_taxa_negativa_e_recusada():
    with pytest.raises(ErroDeValidacao, match="Taxa de juros"):
        antecipar_quantidade(PARCELA, Decimal("-0.01"), 10, 1)


@pytest.mark.parametrize("quantidade", [-1, 11])
def test_quantidade_fora_do_intervalo(quantidade):
    with pytest.raises(ErroDeValidacao, match="Parcelas a antecipar"):
        antecipar_quantidade(PARCELA, DOIS_POR_CENTO, 10, quantidade)


def test_parcelas_restantes_negativas():
    with pytest.raises(ErroDeValidacao, match="Parcelas restantes"):
        antecipar_quantidade(PARCELA, DOIS_POR_CENTO, -1, 0)


@pytest.mark.parametrize("valor", [Decimal(0), Decimal(-1)])
def test_valor_disponivel_precisa_ser_positivo(valor):
    with pytest.raises(ErroDeValidacao, match="Valor disponível"):
        antecipar_com_valor(PARCELA, DOIS_POR_CENTO, 10, valor)
