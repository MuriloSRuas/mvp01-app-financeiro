from datetime import date, datetime
from decimal import Decimal

import pytest

from financas.core.dinheiro import ErroDeValidacao
from financas.core.gastos import (
    ENTRADA,
    SAIDA,
    SEM_CATEGORIA,
    Lancamento,
    formatar_data,
    ler_data,
    novo_lancamento,
    resumir,
)

OUTUBRO = (date(2026, 10, 1), date(2026, 10, 31))


def _l(tipo, valor, dia, categoria, mes=10):
    return novo_lancamento(tipo, Decimal(valor), date(2026, mes, dia), categoria)


# --- Lançamento (RF07) ----------------------------------------------------------


def test_lancamento_valido():
    l = novo_lancamento(SAIDA, Decimal("45.90"), date(2026, 10, 5), "Mercado", "feira")
    assert (l.tipo, l.valor, l.categoria, l.descricao, l.id) == (SAIDA, Decimal("45.90"), "Mercado", "feira", None)
    assert l.eh_saida


def test_categoria_vazia_vira_sem_categoria():
    assert novo_lancamento(SAIDA, Decimal(10), date(2026, 1, 1), "   ").categoria == SEM_CATEGORIA


def test_espacos_extras_sao_removidos():
    l = novo_lancamento(SAIDA, Decimal(10), date(2026, 1, 1), "  Mercado   do  bairro ", "  pão  ")
    assert l.categoria == "Mercado do bairro"
    assert l.descricao == "pão"


@pytest.mark.parametrize("valor", [Decimal(0), Decimal("-5")])
def test_valor_precisa_ser_positivo(valor):
    with pytest.raises(ErroDeValidacao, match="Valor: precisa ser maior que zero"):
        novo_lancamento(SAIDA, valor, date(2026, 1, 1), "X")


def test_valor_com_fracao_de_centavo():
    with pytest.raises(ErroDeValidacao, match="2 casas decimais"):
        novo_lancamento(SAIDA, Decimal("1.005"), date(2026, 1, 1), "X")


def test_tipo_invalido():
    with pytest.raises(ErroDeValidacao, match="Tipo"):
        novo_lancamento("transferencia", Decimal(1), date(2026, 1, 1), "X")


def test_categoria_vazia_direto_no_construtor_e_recusada():
    with pytest.raises(ErroDeValidacao, match="Categoria"):
        Lancamento(SAIDA, Decimal(1), date(2026, 1, 1), "")


def test_data_precisa_ser_date():
    with pytest.raises(TypeError):
        Lancamento(SAIDA, Decimal(1), "2026-01-01", "X")
    with pytest.raises(TypeError):
        Lancamento(SAIDA, Decimal(1), datetime(2026, 1, 1, 10, 0), "X")


# --- Datas -------------------------------------------------------------------------


def test_ler_data_brasileira():
    assert ler_data("31/10/2026") == date(2026, 10, 31)
    assert ler_data(" 5/1/2026 ") == date(2026, 1, 5)


@pytest.mark.parametrize("texto", ["2026-10-31", "31/10/26", "31-10-2026", "hoje"])
def test_ler_data_formato_invalido(texto):
    with pytest.raises(ErroDeValidacao, match="DD/MM/AAAA"):
        ler_data(texto)


def test_ler_data_inexistente():
    with pytest.raises(ErroDeValidacao, match="31/02/2026 não existe"):
        ler_data("31/02/2026")


def test_ler_data_vazia():
    with pytest.raises(ErroDeValidacao, match="campo obrigatório"):
        ler_data("")


def test_formatar_data():
    assert formatar_data(date(2026, 1, 5)) == "05/01/2026"


# --- Resumo do período (RF11 / regra 6.3) -----------------------------------------


def test_totais_e_saldo():
    resumo = resumir(
        [_l(ENTRADA, "5000.00", 1, "Salário"), _l(SAIDA, "1200.00", 5, "Aluguel"), _l(SAIDA, "300.50", 7, "Mercado")],
        *OUTUBRO,
    )
    assert resumo.total_entradas == Decimal("5000.00")
    assert resumo.total_saidas == Decimal("1500.50")
    assert resumo.saldo == Decimal("3499.50")


def test_saldo_negativo():
    resumo = resumir([_l(ENTRADA, "100", 1, "X"), _l(SAIDA, "250", 2, "Y")], *OUTUBRO)
    assert resumo.saldo == Decimal("-150")


def test_ranking_so_de_saidas_em_ordem_decrescente():
    resumo = resumir(
        [
            _l(ENTRADA, "9999", 1, "Salário"),
            _l(SAIDA, "100", 2, "Lazer"),
            _l(SAIDA, "250", 3, "Mercado"),
            _l(SAIDA, "150", 4, "Mercado"),
            _l(SAIDA, "500", 5, "Aluguel"),
        ],
        *OUTUBRO,
    )
    assert [(i.categoria, i.valor) for i in resumo.ranking] == [
        ("Aluguel", Decimal(500)),
        ("Mercado", Decimal(400)),
        ("Lazer", Decimal(100)),
    ]
    assert [i.percentual for i in resumo.ranking] == [Decimal("0.5"), Decimal("0.4"), Decimal("0.1")]


def test_ranking_empate_em_ordem_alfabetica():
    resumo = resumir([_l(SAIDA, "10", 1, "Zebra"), _l(SAIDA, "10", 1, "Abacate")], *OUTUBRO)
    assert [i.categoria for i in resumo.ranking] == ["Abacate", "Zebra"]


def test_sem_saidas_nao_divide_por_zero():
    resumo = resumir([_l(ENTRADA, "100", 1, "Salário")], *OUTUBRO)
    assert resumo.total_saidas == 0
    assert resumo.ranking == ()


def test_periodo_vazio():
    resumo = resumir([], *OUTUBRO)
    assert resumo.lancamentos == ()
    assert resumo.saldo == 0


def test_ignora_lancamentos_fora_do_periodo_e_inclui_as_pontas():
    resumo = resumir(
        [
            _l(SAIDA, "1", 30, "Fora", mes=9),
            _l(SAIDA, "2", 1, "Dentro"),
            _l(SAIDA, "3", 31, "Dentro"),
            _l(SAIDA, "4", 1, "Fora", mes=11),
        ],
        *OUTUBRO,
    )
    assert resumo.total_saidas == Decimal(5)
    assert len(resumo.lancamentos) == 2


def test_lancamentos_ordenados_por_data():
    resumo = resumir([_l(SAIDA, "1", 20, "B"), _l(SAIDA, "1", 3, "A")], *OUTUBRO)
    assert [l.data.day for l in resumo.lancamentos] == [3, 20]


def test_periodo_invertido():
    with pytest.raises(ErroDeValidacao, match="data inicial é depois"):
        resumir([], date(2026, 10, 31), date(2026, 10, 1))
