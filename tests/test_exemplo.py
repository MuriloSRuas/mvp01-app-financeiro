"""Teste de exemplo da Fase 0.

Serve só para provar que o pytest encontra o pacote `financas`. Será
substituído pelos testes reais do núcleo a partir da Fase 1.
"""

import financas


def test_pacote_tem_versao():
    assert financas.__version__ == "0.1.0"
