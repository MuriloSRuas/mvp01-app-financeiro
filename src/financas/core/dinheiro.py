"""Dinheiro e taxas: leitura do que o usuário digita, validação, arredondamento
e formatação no padrão brasileiro (R$ 1.234,56).

Por que `Decimal` e não `float`: o `float` guarda números em binário e erra em
contas simples (0.1 + 0.2 == 0.30000000000000004). Em dinheiro isso vira
centavo sumindo. O `Decimal` calcula em base 10, como no caderno.

Por que não usar o módulo `locale`: ele depende de como o sistema operacional
está configurado (um Ubuntu em inglês formataria 1,234.56). Fazendo à mão, o
resultado é o mesmo em qualquer máquina.
"""

import re
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")

# Número no formato brasileiro: sinal opcional, parte inteira com ou sem
# pontos de milhar (em grupos de 3) e, opcionalmente, vírgula + casas decimais.
# Aceita: 1234 | 1234,56 | 1.234,56 | -0,5     Recusa: 1234.56 | 1.23,4 | 12,
_NUMERO_PT_BR = re.compile(r"^(-)?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?$")


class ErroDeValidacao(ValueError):
    """Entrada inválida do usuário.

    A mensagem já vem pronta para aparecer na tela: a interface só precisa
    capturar este erro e mostrá-lo, sem stack trace e sem fechar o programa.
    """


# ---------------------------------------------------------------------------
# Leitura (texto digitado -> Decimal)
# ---------------------------------------------------------------------------


def ler_decimal(texto: str, campo: str = "Valor") -> Decimal:
    """Converte um número digitado em pt-BR ("1.234,56") para `Decimal`.

    O símbolo "R$" e espaços são ignorados. A vírgula é sempre o separador
    decimal; o ponto, só de milhar. "1234.56" é recusado de propósito: aceitar
    os dois formatos tornaria "1.234" ambíguo (mil duzentos e trinta e quatro
    ou um vírgula dois três quatro?).
    """
    limpo = texto.replace("R$", "").replace(" ", "").strip()
    if not limpo:
        raise ErroDeValidacao(f"{campo}: campo obrigatório.")

    encontrado = _NUMERO_PT_BR.match(limpo)
    if encontrado is None:
        raise ErroDeValidacao(
            f"{campo}: '{texto.strip()}' não é um número válido. "
            "Use vírgula para os centavos, por exemplo 1.234,56."
        )

    sinal, inteiro, decimais = encontrado.groups()
    numero = (sinal or "") + inteiro.replace(".", "")
    if decimais:
        numero += "." + decimais
    return Decimal(numero)


def ler_dinheiro(texto: str, campo: str = "Valor") -> Decimal:
    """Lê um valor em reais. Igual a `ler_decimal`, mas com no máximo 2 casas
    decimais, porque não existe fração de centavo para pagar."""
    valor = ler_decimal(texto, campo)
    if _casas_decimais(valor) > 2:
        raise ErroDeValidacao(f"{campo}: use no máximo 2 casas decimais (centavos).")
    return valor


def ler_taxa_percentual(texto: str, campo: str = "Taxa") -> Decimal:
    """Lê uma taxa digitada em % ao mês e devolve a fração usada nas contas.

    O usuário digita "2" (2% a.m.) e as fórmulas precisam de 0,02. Fazer a
    conversão num lugar só evita esquecer a divisão por 100 em algum cálculo.
    """
    return ler_decimal(texto, campo) / 100


def ler_inteiro(texto: str, campo: str = "Valor") -> int:
    """Lê um número inteiro (ex.: prazo em meses). "12,5" é recusado."""
    valor = ler_decimal(texto, campo)
    if valor != valor.to_integral_value():
        raise ErroDeValidacao(f"{campo}: informe um número inteiro, sem casas decimais.")
    return int(valor)


def _casas_decimais(valor: Decimal) -> int:
    expoente = valor.as_tuple().exponent
    return max(0, -expoente)


# ---------------------------------------------------------------------------
# Validação (usada pelas regras de negócio)
# ---------------------------------------------------------------------------


def exigir_positivo(valor: Decimal, campo: str) -> None:
    """Garante valor > 0. Também recusa `float`, para nenhum chegar às contas."""
    _exigir_decimal(valor, campo)
    if valor <= 0:
        raise ErroDeValidacao(f"{campo}: precisa ser maior que zero.")


def exigir_nao_negativo(valor: Decimal, campo: str) -> None:
    """Garante valor >= 0 (ex.: taxa 0% é válida, taxa negativa não)."""
    _exigir_decimal(valor, campo)
    if valor < 0:
        raise ErroDeValidacao(f"{campo}: não pode ser negativo.")


def exigir_inteiro(valor: int, campo: str, minimo: int, maximo: int | None = None) -> None:
    """Garante que `valor` é um `int` dentro do intervalo [minimo, maximo]."""
    # bool é subclasse de int em Python (True == 1); aqui não faz sentido.
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ErroDeValidacao(f"{campo}: informe um número inteiro.")
    if valor < minimo:
        raise ErroDeValidacao(f"{campo}: precisa ser no mínimo {minimo}.")
    if maximo is not None and valor > maximo:
        raise ErroDeValidacao(f"{campo}: precisa ser no máximo {maximo}.")


def _exigir_decimal(valor: Decimal, campo: str) -> None:
    # Erro de programação, não do usuário: por isso TypeError, não ErroDeValidacao.
    if not isinstance(valor, Decimal):
        raise TypeError(f"{campo}: use Decimal, não {type(valor).__name__}.")


# ---------------------------------------------------------------------------
# Arredondamento
# ---------------------------------------------------------------------------


def arredondar(valor: Decimal) -> Decimal:
    """Arredonda ao centavo do jeito da escola: 0,005 vira 0,01 (ROUND_HALF_UP).

    Use só na hora de mostrar um valor; as contas intermediárias mantêm a
    precisão total.
    """
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def arredondar_para_cima(valor: Decimal) -> Decimal:
    """Arredonda para o centavo de cima (ex.: aporte de 33,333... vira 33,34).

    Usado no aporte mensal: arredondar para baixo deixaria a meta alguns
    centavos abaixo do objetivo no fim do prazo.
    """
    return valor.quantize(CENTAVO, rounding=ROUND_CEILING)


# ---------------------------------------------------------------------------
# Formatação (Decimal -> texto pt-BR)
# ---------------------------------------------------------------------------


def formatar_numero(valor: Decimal, casas: int = 2) -> str:
    """Formata no padrão brasileiro: 1234.5 -> "1.234,50"."""
    arredondado = valor.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    sinal = "-" if arredondado < 0 else ""
    inteiro, _, fracao = f"{abs(arredondado):f}".partition(".")
    # O formato "," do Python sempre usa vírgula de milhar; trocamos por ponto.
    inteiro_com_milhar = f"{int(inteiro):,}".replace(",", ".")
    if casas > 0:
        return f"{sinal}{inteiro_com_milhar},{fracao}"
    return f"{sinal}{inteiro_com_milhar}"


def formatar_reais(valor: Decimal) -> str:
    """Formata em reais: 1234.5 -> "R$ 1.234,50"; -10 -> "-R$ 10,00"."""
    texto = formatar_numero(valor, 2)
    if texto.startswith("-"):
        return f"-R$ {texto[1:]}"
    return f"R$ {texto}"


def formatar_percentual(fracao: Decimal, casas: int = 2) -> str:
    """Formata uma fração como percentual: 0.005 -> "0,50%"."""
    return f"{formatar_numero(fracao * 100, casas)}%"


def formatar_taxa(fracao: Decimal) -> str:
    """Formata uma taxa com as casas que ela tiver: 0.02 -> "2%", 0.00125 -> "0,125%".

    Diferente de `formatar_percentual`, não arredonda: nos "dados informados"
    do relatório a taxa precisa aparecer exatamente como o usuário digitou.
    """
    percentual = (fracao * 100).normalize()
    return f"{formatar_numero(percentual, _casas_decimais(percentual))}%"
