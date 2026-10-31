"""Testes do repositório SQLite. Cada teste usa um banco novo: na memória
(`:memory:`) ou num arquivo dentro da pasta temporária `tmp_path`."""

import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from financas.core.dinheiro import ErroDeValidacao
from financas.core.gastos import ENTRADA, SAIDA, Lancamento, novo_lancamento
from financas.storage.caminhos import NOME_BANCO, caminho_banco, pasta_dados
from financas.storage.repositorio import RepositorioLancamentos, periodo_do_mes


@pytest.fixture
def repo():
    """Fixture: o pytest cria o repositório antes do teste e fecha depois."""
    with RepositorioLancamentos(":memory:") as repositorio:
        yield repositorio


def _l(valor="10.00", dia=1, mes=10, categoria="Mercado", tipo=SAIDA, descricao=""):
    return novo_lancamento(tipo, Decimal(valor), date(2026, mes, dia), categoria, descricao)


# --- CRUD ------------------------------------------------------------------------


def test_adicionar_devolve_com_id_e_grava(repo):
    salvo = repo.adicionar(_l("45.90", descricao="feira"))
    assert salvo.id is not None
    assert repo.obter(salvo.id) == salvo


def test_ids_diferentes(repo):
    assert repo.adicionar(_l()).id != repo.adicionar(_l()).id


def test_valor_volta_identico_sem_erro_de_centavo(repo):
    for valor in ("0.01", "0.10", "19.99", "1234567.89", "100"):
        salvo = repo.adicionar(_l(valor))
        assert repo.obter(salvo.id).valor == Decimal(valor)


def test_valor_gravado_em_centavos(repo):
    salvo = repo.adicionar(_l("12.34"))
    bruto = repo._conexao.execute("SELECT valor_centavos, data FROM lancamentos WHERE id = ?", (salvo.id,)).fetchone()
    assert bruto == (1234, "2026-10-01")


def test_atualizar(repo):
    salvo = repo.adicionar(_l("10.00"))
    editado = Lancamento(ENTRADA, Decimal("20.00"), date(2026, 11, 2), "Salário", "ajuste", salvo.id)
    repo.atualizar(editado)
    assert repo.obter(salvo.id) == editado


def test_atualizar_sem_id(repo):
    with pytest.raises(ValueError):
        repo.atualizar(_l())


def test_atualizar_inexistente(repo):
    with pytest.raises(ErroDeValidacao, match="não encontrado"):
        repo.atualizar(Lancamento(SAIDA, Decimal(1), date(2026, 1, 1), "X", "", 999))


def test_excluir(repo):
    salvo = repo.adicionar(_l())
    repo.excluir(salvo.id)
    with pytest.raises(ErroDeValidacao, match="não encontrado"):
        repo.obter(salvo.id)


def test_excluir_inexistente(repo):
    with pytest.raises(ErroDeValidacao, match="não encontrado"):
        repo.excluir(999)


# --- Filtros (RF10) ------------------------------------------------------------------


def test_listar_mes_filtra_e_ordena(repo):
    repo.adicionar(_l(dia=30, mes=9))
    b = repo.adicionar(_l(dia=31, mes=10))
    a = repo.adicionar(_l(dia=1, mes=10))
    repo.adicionar(_l(dia=1, mes=11))
    assert repo.listar_mes(2026, 10) == [a, b]


def test_listar_mes_vazio(repo):
    assert repo.listar_mes(2026, 10) == []


def test_listar_periodo_inclui_as_pontas(repo):
    a = repo.adicionar(_l(dia=5))
    b = repo.adicionar(_l(dia=10))
    repo.adicionar(_l(dia=11))
    assert repo.listar_periodo(date(2026, 10, 5), date(2026, 10, 10)) == [a, b]


def test_periodo_do_mes():
    assert periodo_do_mes(2026, 10) == (date(2026, 10, 1), date(2026, 10, 31))
    assert periodo_do_mes(2028, 2) == (date(2028, 2, 1), date(2028, 2, 29))  # bissexto
    assert periodo_do_mes(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))


@pytest.mark.parametrize("mes", [0, 13])
def test_mes_invalido(mes):
    with pytest.raises(ErroDeValidacao, match="Mês"):
        periodo_do_mes(2026, mes)


# --- Categorias (RF09) ----------------------------------------------------------------


def test_categorias_sem_repeticao_em_ordem_alfabetica(repo):
    for categoria in ("Mercado", "aluguel", "Mercado", "Lazer"):
        repo.adicionar(_l(categoria=categoria))
    assert repo.categorias() == ["aluguel", "Lazer", "Mercado"]


# --- Banco garante as regras (CHECK) ------------------------------------------------


@pytest.mark.parametrize(
    "valores",
    [
        ("transferencia", 100, "2026-01-01", "X", ""),
        ("saida", 0, "2026-01-01", "X", ""),
        ("saida", -5, "2026-01-01", "X", ""),
        ("saida", 100, "2026-01-01", "", ""),
    ],
)
def test_banco_recusa_dados_invalidos_mesmo_sem_passar_pelo_core(repo, valores):
    with pytest.raises(sqlite3.IntegrityError):
        repo._conexao.execute(
            "INSERT INTO lancamentos (tipo, valor_centavos, data, categoria, descricao) VALUES (?, ?, ?, ?, ?)",
            valores,
        )


# --- Arquivo em disco ------------------------------------------------------------------


def test_dados_persistem_no_arquivo_e_cria_a_pasta(tmp_path):
    caminho = tmp_path / "pasta" / "nova" / NOME_BANCO
    with RepositorioLancamentos(caminho) as repo:
        salvo = repo.adicionar(_l("99.99"))
    with RepositorioLancamentos(caminho) as reaberto:
        assert reaberto.obter(salvo.id) == salvo


# --- Caminho por sistema operacional --------------------------------------------------


def test_pasta_dados_linux_padrao():
    assert pasta_dados("linux", {}, Path("/home/ana")) == Path("/home/ana/.local/share/financas")


def test_pasta_dados_linux_com_xdg():
    assert pasta_dados("linux", {"XDG_DATA_HOME": "/dados"}, Path("/home/ana")) == Path("/dados/financas")


def test_pasta_dados_windows():
    ambiente = {"APPDATA": r"C:\Users\Ana\AppData\Roaming"}
    assert pasta_dados("win32", ambiente, Path("/x")) == Path(r"C:\Users\Ana\AppData\Roaming") / "financas"


def test_pasta_dados_windows_sem_appdata():
    assert pasta_dados("win32", {}, Path("/home/ana")) == Path("/home/ana/AppData/Roaming/financas")


def test_caminho_banco_no_sistema_atual():
    assert caminho_banco().name == NOME_BANCO
    assert caminho_banco().parent.name == "financas"
