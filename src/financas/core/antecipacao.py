"""Antecipação de parcelas: quanto economizo pagando hoje as últimas parcelas.

Ideia: uma parcela que só venceria daqui a `j` meses embute `j` meses de juros.
Pagando-a hoje, pago o **valor presente** dela, que tira esses juros:

    VP(j) = P / (1 + i)^j        economia(j) = P - VP(j)

Hoje (mês 0) o usuário paga a parcela atual normalmente; das `m` restantes,
antecipamos as **últimas** (maiores `j`), porque são as que mais embutem juros.

Premissas: parcelas iguais e taxa mensal constante. O desconto real depende do
contrato e do credor; por isso o relatório sempre traz um aviso de estimativa.
Fórmula confirmada com o usuário na Fase 1.
"""

from dataclasses import dataclass
from decimal import Decimal

from financas.core.dinheiro import (
    arredondar,
    exigir_inteiro,
    exigir_nao_negativo,
    exigir_positivo,
)


@dataclass(frozen=True)
class LinhaAntecipacao:
    """Uma parcela antecipada.

    Valores já arredondados ao centavo: `valor_presente` é o que se paga de
    fato, e `economia` é calculada a partir dele, para que cada linha feche
    (valor_presente + economia == valor_parcela).
    """

    vence_em_meses: int
    valor_parcela: Decimal
    valor_presente: Decimal
    economia: Decimal


@dataclass(frozen=True)
class ResultadoAntecipacao:
    """Resultado do RF03 (quantidade informada) ou do RF04 (valor disponível).

    `valor_disponivel` só é preenchido no RF04. Os totais somam os valores já
    arredondados de cada linha, para o relatório fechar visualmente.
    """

    valor_parcela: Decimal
    taxa: Decimal
    parcelas_restantes: int
    linhas: tuple[LinhaAntecipacao, ...]
    valor_disponivel: Decimal | None = None

    @property
    def quantidade(self) -> int:
        return len(self.linhas)

    @property
    def total_a_pagar(self) -> Decimal:
        return sum((linha.valor_presente for linha in self.linhas), Decimal("0.00"))

    @property
    def total_economia(self) -> Decimal:
        return sum((linha.economia for linha in self.linhas), Decimal("0.00"))

    @property
    def sobra(self) -> Decimal | None:
        """Quanto do valor disponível não foi usado (só no RF04)."""
        if self.valor_disponivel is None:
            return None
        return self.valor_disponivel - self.total_a_pagar


def valor_presente(valor_parcela: Decimal, taxa: Decimal, vence_em_meses: int) -> Decimal:
    """VP(j) = P / (1 + i)^j, com precisão total (sem arredondar)."""
    return valor_parcela / (1 + taxa) ** vence_em_meses


def antecipar_quantidade(
    valor_parcela: Decimal, taxa: Decimal, parcelas_restantes: int, quantidade: int
) -> ResultadoAntecipacao:
    """RF03: antecipa as `quantidade` últimas parcelas, da última para trás.

    Com `m` restantes e `q` a antecipar, as parcelas são j = m, m-1, ..., m-q+1.
    """
    _validar(valor_parcela, taxa, parcelas_restantes)
    exigir_inteiro(
        quantidade, "Parcelas a antecipar", minimo=0, maximo=parcelas_restantes
    )

    linhas = tuple(
        _linha(valor_parcela, taxa, j)
        for j in range(parcelas_restantes, parcelas_restantes - quantidade, -1)
    )
    return ResultadoAntecipacao(valor_parcela, taxa, parcelas_restantes, linhas)


def antecipar_com_valor(
    valor_parcela: Decimal, taxa: Decimal, parcelas_restantes: int, valor_disponivel: Decimal
) -> ResultadoAntecipacao:
    """RF04: quantas das últimas parcelas cabem em `valor_disponivel`.

    Soma o valor presente (arredondado) a partir da última parcela e vai para
    trás enquanto o total couber no valor. Como as parcelas mais próximas têm
    valor presente maior, quando uma não cabe as seguintes também não cabem.
    """
    _validar(valor_parcela, taxa, parcelas_restantes)
    exigir_positivo(valor_disponivel, "Valor disponível")

    linhas = []
    total = Decimal(0)
    for j in range(parcelas_restantes, 0, -1):
        linha = _linha(valor_parcela, taxa, j)
        if total + linha.valor_presente > valor_disponivel:
            break
        linhas.append(linha)
        total += linha.valor_presente

    return ResultadoAntecipacao(
        valor_parcela, taxa, parcelas_restantes, tuple(linhas), valor_disponivel
    )


def _linha(valor_parcela: Decimal, taxa: Decimal, vence_em_meses: int) -> LinhaAntecipacao:
    vp = arredondar(valor_presente(valor_parcela, taxa, vence_em_meses))
    return LinhaAntecipacao(vence_em_meses, valor_parcela, vp, valor_parcela - vp)


def _validar(valor_parcela: Decimal, taxa: Decimal, parcelas_restantes: int) -> None:
    exigir_positivo(valor_parcela, "Valor da parcela")
    exigir_nao_negativo(taxa, "Taxa de juros")
    exigir_inteiro(parcelas_restantes, "Parcelas restantes", minimo=0)
