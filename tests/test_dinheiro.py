from decimal import Decimal

import pytest

from financas.core.dinheiro import (
    ErroDeValidacao,
    arredondar,
    arredondar_para_cima,
    exigir_inteiro,
    exigir_nao_negativo,
    exigir_positivo,
    formatar_numero,
    formatar_percentual,
    formatar_reais,
    ler_decimal,
    ler_dinheiro,
    ler_inteiro,
    ler_taxa_percentual,
)

# --- Leitura -----------------------------------------------------------------


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("1234,56", "1234.56"),
        ("1.234,56", "1234.56"),
        ("1.234", "1234"),
        ("1234", "1234"),
        ("1.234.567,89", "1234567.89"),
        ("0,5", "0.5"),
        ("R$ 1.234,56", "1234.56"),
        ("  200,00  ", "200.00"),
        ("-3,5", "-3.5"),
    ],
)
def test_ler_decimal_aceita_formato_brasileiro(texto, esperado):
    assert ler_decimal(texto) == Decimal(esperado)


@pytest.mark.parametrize("texto", ["1234.56", "1.23,4", "12,", "abc", "1,2,3", "--1", "1.2345"])
def test_ler_decimal_recusa_formato_invalido(texto):
    with pytest.raises(ErroDeValidacao, match="não é um número válido"):
        ler_decimal(texto)


def test_ler_decimal_recusa_campo_vazio_com_nome_do_campo():
    with pytest.raises(ErroDeValidacao, match="Valor da meta: campo obrigatório"):
        ler_decimal("   ", "Valor da meta")


def test_ler_dinheiro_aceita_ate_dois_centavos():
    assert ler_dinheiro("10,5") == Decimal("10.5")
    assert ler_dinheiro("10,55") == Decimal("10.55")


def test_ler_dinheiro_recusa_fracao_de_centavo():
    with pytest.raises(ErroDeValidacao, match="2 casas decimais"):
        ler_dinheiro("10,555")


def test_ler_taxa_converte_percentual_em_fracao():
    assert ler_taxa_percentual("2") == Decimal("0.02")
    assert ler_taxa_percentual("0,5") == Decimal("0.005")
    assert ler_taxa_percentual("0") == 0


def test_ler_inteiro():
    assert ler_inteiro("50") == 50
    assert ler_inteiro("1.200") == 1200


def test_ler_inteiro_recusa_decimal():
    with pytest.raises(ErroDeValidacao, match="número inteiro"):
        ler_inteiro("12,5")


# --- Validação ---------------------------------------------------------------


def test_exigir_positivo():
    exigir_positivo(Decimal("0.01"), "Valor")
    for valor in (Decimal(0), Decimal(-1)):
        with pytest.raises(ErroDeValidacao, match="maior que zero"):
            exigir_positivo(valor, "Valor")


def test_exigir_nao_negativo():
    exigir_nao_negativo(Decimal(0), "Taxa")
    with pytest.raises(ErroDeValidacao, match="Taxa: não pode ser negativo"):
        exigir_nao_negativo(Decimal("-0.01"), "Taxa")


def test_float_e_recusado_nas_contas():
    with pytest.raises(TypeError, match="use Decimal"):
        exigir_positivo(0.1, "Valor")


def test_exigir_inteiro():
    exigir_inteiro(5, "Prazo", minimo=1, maximo=10)
    with pytest.raises(ErroDeValidacao, match="no mínimo 1"):
        exigir_inteiro(0, "Prazo", minimo=1)
    with pytest.raises(ErroDeValidacao, match="no máximo 10"):
        exigir_inteiro(11, "Prazo", minimo=1, maximo=10)
    for nao_inteiro in (Decimal("2.5"), 2.0, True):
        with pytest.raises(ErroDeValidacao, match="número inteiro"):
            exigir_inteiro(nao_inteiro, "Prazo", minimo=1)


# --- Arredondamento ----------------------------------------------------------


def test_arredondar_meio_para_cima():
    assert arredondar(Decimal("0.005")) == Decimal("0.01")
    assert arredondar(Decimal("0.004")) == Decimal("0.00")
    assert arredondar(Decimal("2.675")) == Decimal("2.68")  # float daria 2.67
    assert arredondar(Decimal("410.1741")) == Decimal("410.17")


def test_arredondar_para_cima():
    assert arredondar_para_cima(Decimal("33.3333")) == Decimal("33.34")
    assert arredondar_para_cima(Decimal("200")) == Decimal("200.00")


# --- Formatação --------------------------------------------------------------


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("1234.56", "R$ 1.234,56"),
        ("1234.5", "R$ 1.234,50"),
        ("0", "R$ 0,00"),
        ("0.005", "R$ 0,01"),
        ("1234567.891", "R$ 1.234.567,89"),
        ("-10", "-R$ 10,00"),
        ("-0.001", "R$ 0,00"),  # não mostra "-R$ 0,00"
    ],
)
def test_formatar_reais(valor, esperado):
    assert formatar_reais(Decimal(valor)) == esperado


def test_formatar_numero_com_outras_casas():
    assert formatar_numero(Decimal("12.345"), 1) == "12,3"
    assert formatar_numero(Decimal("1234.5"), 0) == "1.235"


def test_formatar_percentual():
    assert formatar_percentual(Decimal("0.005")) == "0,50%"
    assert formatar_percentual(Decimal("0.125"), 1) == "12,5%"


def test_ida_e_volta():
    assert ler_dinheiro(formatar_reais(Decimal("98765.43"))) == Decimal("98765.43")
