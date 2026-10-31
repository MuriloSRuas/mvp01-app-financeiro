"""Testes do salvamento de relatórios. `tmp_path` é uma pasta temporária que o
pytest cria (e apaga) para cada teste, assim nada é gravado na sua pasta real."""

from datetime import datetime

from financas.reports.arquivo import nome_arquivo, salvar_relatorio


def test_nome_arquivo_com_data_ordenavel():
    assert nome_arquivo("meta-economia", datetime(2026, 1, 5, 9, 7)) == "meta-economia-2026-01-05-0907.md"


def test_salva_em_utf8(tmp_path):
    caminho = salvar_relatorio("# Antecipação\n\nR$ 1.234,56 — ç\n", tmp_path / "relatorio.md")
    assert caminho == tmp_path / "relatorio.md"
    assert caminho.read_text(encoding="utf-8") == "# Antecipação\n\nR$ 1.234,56 — ç\n"


def test_acrescenta_extensao_md_quando_falta(tmp_path):
    assert salvar_relatorio("x", tmp_path / "relatorio").name == "relatorio.md"
    assert salvar_relatorio("x", tmp_path / "relatorio.v2").name == "relatorio.v2.md"
    assert salvar_relatorio("x", tmp_path / "RELATORIO.MD").name == "RELATORIO.MD"


def test_quebra_de_linha_sempre_lf(tmp_path):
    caminho = salvar_relatorio("a\nb\n", tmp_path / "r.md")
    assert caminho.read_bytes() == b"a\nb\n"


def test_sobrescreve_arquivo_existente(tmp_path):
    caminho = tmp_path / "r.md"
    salvar_relatorio("antigo", caminho)
    salvar_relatorio("novo", caminho)
    assert caminho.read_text(encoding="utf-8") == "novo"
