"""Testes dos relatórios: conferem trechos esperados (parâmetros, fórmula,
passo a passo, resultado e aviso), não o texto inteiro. Assim um ajuste de
redação não quebra todos os testes, mas a falta de uma informação quebra."""

import re
from datetime import datetime
from decimal import Decimal

import pytest

from financas.core.antecipacao import antecipar_com_valor, antecipar_quantidade
from financas.core.meta_economia import calcular_aporte, calcular_meses
from financas.reports.markdown import (
    relatorio_antecipacao,
    relatorio_aporte,
    relatorio_meses,
)

MOMENTO = datetime(2026, 10, 31, 14, 5)
SECOES = ["## Dados informados", "## Fórmula", "## Passo a passo", "## Resultado", "> [!warning]"]


def _gerar_todos():
    return {
        "meses sem juros": relatorio_meses(calcular_meses(Decimal(10000), Decimal(200)), MOMENTO),
        "meses com juros": relatorio_meses(
            calcular_meses(Decimal(10000), Decimal(200), Decimal("0.005")), MOMENTO
        ),
        "aporte sem juros": relatorio_aporte(calcular_aporte(Decimal(10000), 50), MOMENTO),
        "aporte com juros": relatorio_aporte(
            calcular_aporte(Decimal(10000), 45, Decimal("0.005")), MOMENTO
        ),
        "antecipação": relatorio_antecipacao(
            antecipar_quantidade(Decimal(500), Decimal("0.02"), 10, 3), MOMENTO
        ),
        "antecipação por valor": relatorio_antecipacao(
            antecipar_com_valor(Decimal(500), Decimal("0.02"), 10, Decimal(1000)), MOMENTO
        ),
    }


# --- Estrutura comum (RF05) ---------------------------------------------------


@pytest.mark.parametrize("nome, texto", _gerar_todos().items())
def test_todo_relatorio_tem_as_secoes_na_ordem(nome, texto):
    posicoes = [texto.index(secao) for secao in SECOES]
    assert posicoes == sorted(posicoes), nome


@pytest.mark.parametrize("nome, texto", _gerar_todos().items())
def test_todo_relatorio_tem_titulo_data_e_aviso_de_estimativa(nome, texto):
    assert texto.startswith("# ")
    assert "Gerado em 31/10/2026 às 14:05." in texto
    assert "**estimativa**" in texto


@pytest.mark.parametrize("nome, texto", _gerar_todos().items())
def test_markdown_valido_para_o_obsidian(nome, texto):
    linhas = texto.split("\n")
    assert texto.endswith("\n")
    assert texto.count("```") % 2 == 0, "bloco de código sem fechar"
    for numero, linha in enumerate(linhas):
        # Tabela precisa de linha em branco antes, senão vira parágrafo.
        if linha.startswith("|") and not linhas[numero - 1].startswith("|"):
            assert linhas[numero - 1] == "", f"{nome}: tabela sem linha em branco antes"
            assert re.fullmatch(r"\|(---\|)+", linhas[numero + 1]), f"{nome}: tabela sem separador"
        # Toda linha de uma tabela tem o mesmo número de colunas do cabeçalho.
        if linha.startswith("|"):
            inicio = numero
            while inicio > 0 and linhas[inicio - 1].startswith("|"):
                inicio -= 1
            assert linha.count("|") == linhas[inicio].count("|"), f"{nome}: colunas desiguais"


def test_data_atual_quando_nao_informada():
    texto = relatorio_meses(calcular_meses(Decimal(100), Decimal(50)))
    assert f"Gerado em {datetime.now():%d/%m/%Y}" in texto


# --- Meta de economia: meses (RF01) --------------------------------------------


def test_meses_sem_juros():
    texto = _gerar_todos()["meses sem juros"]
    assert "| Valor da meta (M) | R$ 10.000,00 |" in texto
    assert "| Aporte mensal (A) | R$ 200,00 |" in texto
    assert "| Rentabilidade (i) | 0% ao mês |" in texto
    assert "meses = M / A" in texto
    assert "M / A = 10.000,00 / 200,00 = 50" in texto
    assert "**50 meses (4 anos e 2 meses)**" in texto
    assert "render no mês seguinte" not in texto


def test_meses_sem_juros_divisao_nao_exata_explica_arredondamento():
    texto = relatorio_meses(calcular_meses(Decimal(1000), Decimal(300)), MOMENTO)
    assert "≈ 3,33 → arredondando para cima: 4 meses" in texto
    assert "**4 meses**" in texto


def test_meses_com_juros():
    texto = _gerar_todos()["meses com juros"]
    assert "| Rentabilidade (i) | 0,5% ao mês |" in texto
    assert "saldo do mês = saldo anterior × (1 + i) + A" in texto
    assert "No mês 44 o saldo é R$ 9.815,75, ainda abaixo da meta; no mês 45 chega a R$ 10.064,83." in texto
    assert "**45 meses (3 anos e 9 meses)**" in texto
    # Resumo fecha: aportes + rendimentos = saldo final.
    assert "| Total guardado (aportes) | R$ 9.000,00 |" in texto
    assert "| Total de rendimentos | R$ 1.064,83 |" in texto
    assert "| **Saldo final** | **R$ 10.064,83** |" in texto


def test_meses_com_juros_atingida_no_primeiro_mes():
    texto = relatorio_meses(calcular_meses(Decimal(100), Decimal(500), Decimal("0.01")), MOMENTO)
    assert "Já no primeiro mês o saldo (R$ 500,00) alcança a meta." in texto
    assert "**1 mês**" in texto


def test_tabela_curta_aparece_inteira():
    texto = relatorio_meses(calcular_meses(Decimal(2400), Decimal(100)), MOMENTO)  # 24 meses
    assert "| 13 | R$ 100,00 |" in texto
    assert "Tabela resumida" not in texto
    assert "**24 meses (2 anos)**" in texto


def test_tabela_longa_e_resumida_com_aviso():
    texto = _gerar_todos()["meses com juros"]  # 45 meses
    assert "| 12 | R$ 200,00 |" in texto
    assert "| 13 | R$ 200,00 |" not in texto
    assert "| 24 | R$ 200,00 |" in texto
    assert "| 36 | R$ 200,00 |" in texto
    assert "| 45 | R$ 200,00 | R$ 49,08 | R$ 10.064,83 |" in texto
    assert "_Tabela resumida: mostra os 12 primeiros meses, o fim de cada ano e o último mês (15 de 45 meses)._" in texto


# --- Meta de economia: aporte (RF02) ------------------------------------------


def test_aporte_sem_juros():
    texto = _gerar_todos()["aporte sem juros"]
    assert "| Prazo (n) | 50 meses |" in texto
    assert "A = M / n" in texto
    assert "1. A = 10.000,00 / 50 = 200,0000" in texto
    assert "2. Arredondando para cima: **R$ 200,00**" in texto
    assert "**R$ 200,00 por mês**" in texto


def test_aporte_com_juros_mostra_cada_passo():
    texto = _gerar_todos()["aporte com juros"]
    assert "A = M × i / ((1 + i)^n − 1)" in texto
    assert "1. (1 + i)^n = (1 + 0,005)^45 = 1,251621" in texto
    assert "2. (1 + i)^n − 1 = 0,251621" in texto
    assert "3. M × i = 10.000,00 × 0,005 = 50,0000" in texto
    assert "4. A = 50,0000 / 0,251621 = 198,7117" in texto
    assert "5. Arredondando para cima: **R$ 198,72**" in texto
    assert "**R$ 198,72 por mês**" in texto
    assert "| **Saldo final** | **R$ 10.000,42** |" in texto


def test_aporte_prazo_de_um_mes_no_singular():
    texto = relatorio_aporte(calcular_aporte(Decimal(100), 1), MOMENTO)
    assert "| Prazo (n) | 1 mês |" in texto


# --- Antecipação (RF03 e RF04) --------------------------------------------------


def test_antecipacao_por_quantidade():
    texto = _gerar_todos()["antecipação"]
    assert "| Valor da parcela (P) | R$ 500,00 |" in texto
    assert "| Juros do contrato (i) | 2% ao mês |" in texto
    assert "| Parcelas restantes, além da atual (m) | 10 |" in texto
    assert "| Parcelas a antecipar | 3 |" in texto
    assert "valor a pagar hoje = P / (1 + i)^j" in texto
    assert "| 10 meses | 500,00 / 1,02^10 | R$ 410,17 | R$ 89,83 |" in texto
    assert "| 8 meses | 500,00 / 1,02^8 | R$ 426,75 | R$ 73,25 |" in texto
    assert "| **Total** |  | **R$ 1.255,30** | **R$ 244,70** |" in texto
    assert "**Pagando R$ 1.255,30 hoje, você economiza R$ 244,70 em juros.**" in texto
    assert "as que venceriam em 10, 9 e 8 meses" in texto
    assert "as 7 que vencem de 1 a 7 meses" in texto
    assert "Sobram" not in texto


def test_antecipacao_por_valor_explica_por_que_parou():
    texto = _gerar_todos()["antecipação por valor"]
    assert "| Valor disponível para antecipar | R$ 1.000,00 |" in texto
    assert "| Parcelas a antecipar |" not in texto
    assert "A próxima parcela (vence em 8 meses) custaria R$ 426,75 hoje e não cabe no que sobra (R$ 171,45)." in texto
    assert "Sobram R$ 171,45 do valor disponível." in texto


def test_antecipacao_por_valor_que_paga_todas():
    texto = relatorio_antecipacao(antecipar_com_valor(Decimal(500), Decimal("0.02"), 2, Decimal(5000)), MOMENTO)
    assert "Todas as parcelas restantes couberam no valor disponível." in texto
    assert "só a parcela atual (paga hoje); não resta nenhuma outra" in texto


def test_antecipacao_de_uma_parcela_no_singular():
    texto = relatorio_antecipacao(antecipar_quantidade(Decimal(500), Decimal("0.02"), 2, 1), MOMENTO)
    assert "Isso quita a parcela que venceria em 2 meses" in texto
    assert "a parcela atual (paga hoje) e a que vence em 1 mês" in texto


def test_antecipacao_de_nenhuma_parcela():
    texto = relatorio_antecipacao(antecipar_quantidade(Decimal(500), Decimal("0.02"), 10, 0), MOMENTO)
    assert texto.count("Nenhuma parcela antecipada.") == 2  # passo a passo e resultado
    assert "| **Total** |" not in texto
