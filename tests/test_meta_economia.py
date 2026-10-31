from decimal import Decimal

import pytest

from financas.core.dinheiro import ErroDeValidacao, arredondar
from financas.core.meta_economia import (
    LIMITE_MESES,
    MetaInalcancavel,
    calcular_aporte,
    calcular_meses,
    simular,
)

META = Decimal("10000.00")
APORTE = Decimal("200.00")
MEIO_POR_CENTO = Decimal("0.005")

# --- Exemplos oficiais do plano (seção 6.1) ----------------------------------


def test_exemplo_6_1_a_sem_juros_50_meses():
    resultado = calcular_meses(META, APORTE)
    assert resultado.meses == 50
    assert len(resultado.tabela) == 50
    assert resultado.tabela[-1].saldo == META


def test_exemplo_6_1_b_com_juros_45_meses():
    resultado = calcular_meses(META, APORTE, MEIO_POR_CENTO)
    assert resultado.meses == 45
    # Saldos pela fórmula do plano (o texto do plano trazia ≈ 9.821 e ≈ 10.071,
    # aproximações; os valores exatos estão em docs/fase-1.md).
    assert arredondar(resultado.tabela[43].saldo) == Decimal("9815.75")  # mês 44
    assert arredondar(resultado.tabela[44].saldo) == Decimal("10064.83")  # mês 45


def test_exemplo_6_1_c_aporte_200():
    resultado = calcular_aporte(META, 50)
    assert resultado.aporte == Decimal("200.00")


# --- RF01: meses ------------------------------------------------------------


def test_meses_sem_juros_arredonda_para_cima():
    # 1000 / 300 = 3,33 meses -> são necessários 4 aportes.
    assert calcular_meses(Decimal(1000), Decimal(300)).meses == 4


def test_aporte_maior_que_a_meta_leva_um_mes():
    assert calcular_meses(Decimal(100), Decimal(500), MEIO_POR_CENTO).meses == 1


def test_tabela_com_juros_mostra_rendimento_sobre_saldo_anterior():
    tabela = calcular_meses(META, APORTE, MEIO_POR_CENTO).tabela
    # Mês 1: saldo anterior 0, então não rende; o aporte só rende no mês 2.
    assert tabela[0].rendimento == 0
    assert tabela[0].saldo == Decimal(200)
    assert tabela[1].rendimento == Decimal("1.000")
    assert tabela[1].saldo == Decimal("401.000")


def test_meta_inalcancavel_com_juros():
    with pytest.raises(MetaInalcancavel, match="não é atingida em 1200 meses"):
        calcular_meses(Decimal(1_000_000), Decimal("0.01"), Decimal("0.0001"))


def test_meta_inalcancavel_sem_juros():
    with pytest.raises(MetaInalcancavel, match="não é atingida em 1200 meses"):
        calcular_meses(Decimal(1_000_000), Decimal("0.01"))


def test_meta_no_limite_exato_e_alcancavel():
    assert calcular_meses(Decimal(1200), Decimal(1)).meses == LIMITE_MESES


def test_meta_inalcancavel_e_erro_de_validacao():
    # A interface trata os dois do mesmo jeito: mostra a mensagem.
    assert issubclass(MetaInalcancavel, ErroDeValidacao)


# --- RF02: aporte -----------------------------------------------------------


def test_aporte_sem_juros_arredonda_para_cima():
    resultado = calcular_aporte(Decimal(100), 3)
    assert resultado.aporte == Decimal("33.34")
    assert resultado.tabela[-1].saldo >= Decimal(100)


def test_aporte_com_juros():
    resultado = calcular_aporte(META, 45, MEIO_POR_CENTO)
    # 10000 * 0,005 / (1,005^45 - 1) = 198,7116...
    assert arredondar(resultado.aporte_exato) == Decimal("198.71")
    assert resultado.aporte == Decimal("198.72")
    assert len(resultado.tabela) == 45
    assert resultado.tabela[-1].saldo >= META


def test_aporte_arredondado_para_cima_nunca_fica_abaixo_da_meta():
    for prazo in (1, 7, 13, 60, 360):
        resultado = calcular_aporte(Decimal("12345.67"), prazo, Decimal("0.0123"))
        assert resultado.tabela[-1].saldo >= Decimal("12345.67")


def test_aporte_prazo_no_limite():
    assert len(calcular_aporte(META, LIMITE_MESES).tabela) == LIMITE_MESES


# --- Entradas inválidas -------------------------------------------------------


@pytest.mark.parametrize("meta", [Decimal(0), Decimal(-1)])
def test_meta_precisa_ser_positiva(meta):
    with pytest.raises(ErroDeValidacao, match="Valor da meta"):
        calcular_meses(meta, APORTE)
    with pytest.raises(ErroDeValidacao, match="Valor da meta"):
        calcular_aporte(meta, 10)


@pytest.mark.parametrize("aporte", [Decimal(0), Decimal(-1)])
def test_aporte_precisa_ser_positivo(aporte):
    with pytest.raises(ErroDeValidacao, match="Aporte mensal"):
        calcular_meses(META, aporte)


def test_taxa_negativa_e_recusada():
    with pytest.raises(ErroDeValidacao, match="Taxa de rentabilidade"):
        calcular_meses(META, APORTE, Decimal("-0.01"))
    with pytest.raises(ErroDeValidacao, match="Taxa de rentabilidade"):
        calcular_aporte(META, 10, Decimal("-0.01"))


@pytest.mark.parametrize("prazo", [0, -5, LIMITE_MESES + 1, Decimal("12.5"), 12.0])
def test_prazo_invalido(prazo):
    with pytest.raises(ErroDeValidacao, match="Prazo em meses"):
        calcular_aporte(META, prazo)


def test_simular_zero_meses_gera_tabela_vazia():
    assert simular(APORTE, Decimal(0), 0) == ()
