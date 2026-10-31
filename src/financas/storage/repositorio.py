"""Guarda e busca os lançamentos de gastos num arquivo SQLite (RF07 a RF10).

SQLite é um banco de dados inteiro dentro de **um arquivo**: não tem servidor
para instalar nem senha, e o módulo `sqlite3` já vem com o Python. Funciona
como o MySQL que você usa com PHP, mas local.

O repositório fala com o resto do programa só em `Lancamento` (do core):
quem chama não vê SQL, e o banco poderia ser trocado sem mexer na tela.

Dinheiro é gravado em **centavos inteiros** (R$ 12,34 -> 1234), porque o
SQLite guardaria um decimal como ponto flutuante e erraria centavos.
"""

import calendar
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from financas.core.dinheiro import ErroDeValidacao, exigir_inteiro
from financas.core.gastos import Lancamento

# CHECK = regras que o próprio banco garante, mesmo que um bug tente gravar
# algo errado. IF NOT EXISTS: só cria a tabela na primeira vez.
_ESQUEMA = """
CREATE TABLE IF NOT EXISTS lancamentos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo           TEXT    NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    data           TEXT    NOT NULL,
    categoria      TEXT    NOT NULL CHECK (categoria <> ''),
    descricao      TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos (data);
"""

_COLUNAS = "id, tipo, valor_centavos, data, categoria, descricao"


class RepositorioLancamentos:
    """Acesso à tabela `lancamentos`.

    Use `":memory:"` como caminho para um banco temporário na memória (testes).
    Também funciona com `with`, que fecha o banco ao sair do bloco.
    """

    def __init__(self, caminho: Path | str) -> None:
        if caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self._conexao = sqlite3.connect(caminho)
        self._conexao.executescript(_ESQUEMA)

    def __enter__(self) -> "RepositorioLancamentos":
        return self

    def __exit__(self, *_erro) -> None:
        self.fechar()

    def fechar(self) -> None:
        self._conexao.close()

    # --- Escrita ------------------------------------------------------------
    # "with self._conexao" abre uma transação: grava tudo ou, se der erro,
    # desfaz tudo (commit/rollback automáticos).

    def adicionar(self, lancamento: Lancamento) -> Lancamento:
        """Grava um lançamento novo e o devolve com o `id` criado pelo banco."""
        with self._conexao:
            cursor = self._conexao.execute(
                "INSERT INTO lancamentos (tipo, valor_centavos, data, categoria, descricao)"
                " VALUES (?, ?, ?, ?, ?)",
                _para_linha(lancamento),
            )
        return _com_id(lancamento, cursor.lastrowid)

    def atualizar(self, lancamento: Lancamento) -> None:
        """Regrava um lançamento existente (RF08: editar)."""
        if lancamento.id is None:
            raise ValueError("Só dá para atualizar um lançamento que já tem id.")
        with self._conexao:
            cursor = self._conexao.execute(
                "UPDATE lancamentos SET tipo = ?, valor_centavos = ?, data = ?, categoria = ?, descricao = ?"
                " WHERE id = ?",
                (*_para_linha(lancamento), lancamento.id),
            )
        _exigir_encontrado(cursor.rowcount)

    def excluir(self, id_lancamento: int) -> None:
        """Apaga um lançamento (RF08). A confirmação ("tem certeza?") é da tela."""
        with self._conexao:
            cursor = self._conexao.execute("DELETE FROM lancamentos WHERE id = ?", (id_lancamento,))
        _exigir_encontrado(cursor.rowcount)

    # --- Leitura ------------------------------------------------------------

    def obter(self, id_lancamento: int) -> Lancamento:
        linha = self._conexao.execute(
            f"SELECT {_COLUNAS} FROM lancamentos WHERE id = ?", (id_lancamento,)
        ).fetchone()
        if linha is None:
            _exigir_encontrado(0)
        return _de_linha(linha)

    def listar_periodo(self, inicio: date, fim: date) -> list[Lancamento]:
        """Lançamentos entre `inicio` e `fim` (inclusive), por data.

        Funciona comparando texto porque a data está no formato ISO
        (AAAA-MM-DD), em que a ordem alfabética é a ordem cronológica.
        """
        linhas = self._conexao.execute(
            f"SELECT {_COLUNAS} FROM lancamentos WHERE data BETWEEN ? AND ? ORDER BY data, id",
            (inicio.isoformat(), fim.isoformat()),
        ).fetchall()
        return [_de_linha(linha) for linha in linhas]

    def listar_mes(self, ano: int, mes: int) -> list[Lancamento]:
        """RF10: lançamentos de um mês/ano."""
        return self.listar_periodo(*periodo_do_mes(ano, mes))

    def categorias(self) -> list[str]:
        """RF09: categorias já usadas, em ordem alfabética, para escolher ao lançar."""
        linhas = self._conexao.execute(
            "SELECT DISTINCT categoria FROM lancamentos ORDER BY categoria COLLATE NOCASE"
        ).fetchall()
        return [categoria for (categoria,) in linhas]


def periodo_do_mes(ano: int, mes: int) -> tuple[date, date]:
    """(primeiro dia, último dia) do mês. Ex.: fevereiro de 2028 -> 01/02 a 29/02."""
    exigir_inteiro(mes, "Mês", minimo=1, maximo=12)
    exigir_inteiro(ano, "Ano", minimo=1, maximo=9999)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo_dia)


def _para_linha(l: Lancamento) -> tuple:
    centavos = int(l.valor * 100)  # exato: o Lancamento garante no máximo 2 casas
    return (l.tipo, centavos, l.data.isoformat(), l.categoria, l.descricao)


def _de_linha(linha: tuple) -> Lancamento:
    id_, tipo, centavos, data_iso, categoria, descricao = linha
    valor = Decimal(centavos).scaleb(-2)  # 1234 -> Decimal("12.34")
    return Lancamento(tipo, valor, date.fromisoformat(data_iso), categoria, descricao, id_)


def _com_id(l: Lancamento, id_: int) -> Lancamento:
    return Lancamento(l.tipo, l.valor, l.data, l.categoria, l.descricao, id_)


def _exigir_encontrado(linhas_afetadas: int) -> None:
    if linhas_afetadas == 0:
        raise ErroDeValidacao("Lançamento não encontrado (pode já ter sido excluído).")
