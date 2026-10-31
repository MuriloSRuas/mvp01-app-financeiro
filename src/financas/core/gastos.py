"""Gastos: o lançamento (entrada ou saída) e o resumo de um período (RF07 e RF11).

Aqui ficam só as regras: o que é um lançamento válido e como calcular
totais, saldo e ranking por categoria. Guardar e buscar no banco é papel de
`storage/repositorio.py`; mostrar é papel da interface e do relatório.

Regras (seção 6.3 do plano):

    saldo      = total de entradas − total de saídas
    percentual = saídas da categoria / total de saídas   (só saídas entram no ranking)
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from financas.core.dinheiro import ErroDeValidacao, exigir_positivo

ENTRADA = "entrada"
SAIDA = "saida"
TIPOS = (ENTRADA, SAIDA)
SEM_CATEGORIA = "Sem categoria"


@dataclass(frozen=True)
class Lancamento:
    """Uma movimentação de dinheiro.

    `id` é `None` enquanto o lançamento não foi gravado; o banco atribui o
    número ao salvar. A validação roda ao criar o objeto, então não existe
    `Lancamento` inválido circulando pelo programa.
    """

    tipo: str
    valor: Decimal
    data: date
    categoria: str
    descricao: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS:
            raise ErroDeValidacao("Tipo: escolha entrada ou saída.")
        exigir_positivo(self.valor, "Valor")
        if self.valor != self.valor.quantize(Decimal("0.01")):
            raise ErroDeValidacao("Valor: use no máximo 2 casas decimais (centavos).")
        # datetime é subclasse de date; aceitar misturaria hora com data.
        if not isinstance(self.data, date) or isinstance(self.data, datetime):
            raise TypeError("Data: use datetime.date.")
        if not self.categoria.strip():
            raise ErroDeValidacao("Categoria: não pode ficar vazia.")

    @property
    def eh_saida(self) -> bool:
        return self.tipo == SAIDA


def novo_lancamento(
    tipo: str, valor: Decimal, data: date, categoria: str, descricao: str = "", id: int | None = None
) -> Lancamento:
    """Cria um lançamento a partir do que o usuário digitou, limpando o texto.

    Categoria vazia vira "Sem categoria" (regra 6.3); espaços sobrando na
    categoria e na descrição são removidos, para "Mercado " e "Mercado" não
    virarem duas categorias diferentes.
    """
    return Lancamento(tipo, valor, data, normalizar_categoria(categoria), _limpar(descricao), id)


def normalizar_categoria(texto: str) -> str:
    return _limpar(texto) or SEM_CATEGORIA


def _limpar(texto: str) -> str:
    # Tira espaços das pontas e junta espaços repetidos no meio.
    return re.sub(r"\s+", " ", texto).strip()


# ---------------------------------------------------------------------------
# Datas: ISO (AAAA-MM-DD) por dentro, DD/MM/AAAA na tela
# ---------------------------------------------------------------------------


def ler_data(texto: str, campo: str = "Data") -> date:
    """Converte "31/10/2026" em `date(2026, 10, 31)`. Recusa datas inexistentes (31/02)."""
    limpo = texto.strip()
    if not limpo:
        raise ErroDeValidacao(f"{campo}: campo obrigatório.")
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", limpo):
        raise ErroDeValidacao(f"{campo}: use o formato DD/MM/AAAA, por exemplo 31/10/2026.")
    dia, mes, ano = (int(parte) for parte in limpo.split("/"))
    try:
        return date(ano, mes, dia)
    except ValueError:
        raise ErroDeValidacao(f"{campo}: {limpo} não existe no calendário.") from None


def formatar_data(data: date) -> str:
    return f"{data:%d/%m/%Y}"


# ---------------------------------------------------------------------------
# Resumo de um período (RF11)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ItemRanking:
    """Uma categoria no ranking de saídas. `percentual` é fração exata (0,4 = 40%)."""

    categoria: str
    valor: Decimal
    percentual: Decimal


@dataclass(frozen=True)
class ResumoPeriodo:
    inicio: date
    fim: date
    lancamentos: tuple[Lancamento, ...]
    total_entradas: Decimal
    total_saidas: Decimal
    ranking: tuple[ItemRanking, ...]

    @property
    def saldo(self) -> Decimal:
        return self.total_entradas - self.total_saidas


def resumir(lancamentos: list[Lancamento], inicio: date, fim: date) -> ResumoPeriodo:
    """Totais, saldo e ranking de saídas por categoria entre `inicio` e `fim` (inclusive).

    Lançamentos fora do período são ignorados. Os valores já estão em
    centavos exatos, então as somas não precisam de arredondamento.
    """
    if inicio > fim:
        raise ErroDeValidacao("Período: a data inicial é depois da data final.")

    do_periodo = tuple(
        sorted((l for l in lancamentos if inicio <= l.data <= fim), key=lambda l: (l.data, l.id or 0))
    )
    total_entradas = sum((l.valor for l in do_periodo if not l.eh_saida), Decimal("0.00"))
    total_saidas = sum((l.valor for l in do_periodo if l.eh_saida), Decimal("0.00"))
    return ResumoPeriodo(
        inicio, fim, do_periodo, total_entradas, total_saidas, _ranking(do_periodo, total_saidas)
    )


def _ranking(lancamentos: tuple[Lancamento, ...], total_saidas: Decimal) -> tuple[ItemRanking, ...]:
    """Saídas somadas por categoria, da maior para a menor.

    Sem saídas no período, o ranking fica vazio, e nunca se divide por zero.
    Empate no valor: ordem alfabética, para o resultado ser sempre o mesmo.
    """
    if total_saidas == 0:
        return ()
    por_categoria: dict[str, Decimal] = {}
    for l in lancamentos:
        if l.eh_saida:
            por_categoria[l.categoria] = por_categoria.get(l.categoria, Decimal(0)) + l.valor
    ordenado = sorted(por_categoria.items(), key=lambda item: (-item[1], item[0]))
    return tuple(ItemRanking(cat, valor, valor / total_saidas) for cat, valor in ordenado)
