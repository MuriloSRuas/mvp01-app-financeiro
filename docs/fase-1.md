# Fase 1: Núcleo de cálculo (sem interface)

## O que foi feito

Escrevi as **contas** do programa, sem janela e sem banco. São três módulos em `src/financas/core/`:

1. **`dinheiro.py`**: lê o que o usuário digita ("1.234,56"), valida, arredonda e formata de volta ("R$ 1.234,56").
2. **`meta_economia.py`**: responde "em quantos meses chego à meta?" (RF01) e "quanto guardo por mês?" (RF02), com a tabela mês a mês.
3. **`antecipacao.py`**: calcula quanto se paga hoje e quanto se economiza antecipando as últimas parcelas, seja pela quantidade (RF03) ou pelo valor disponível (RF04).

Cada módulo tem testes automatizados com os exemplos oficiais do plano (6.1.a, 6.1.b, 6.1.c e 6.2) e casos de borda. São **85 testes** e a cobertura do `core/` é de **100%** (a meta era ≥ 90%).

Ainda não há o que "ver" na tela: na Fase 2 essas contas viram relatórios, e na Fase 3 ganham janela. Dá para experimentar no terminal (veja "Como rodar").

## Mapa dos arquivos

| Arquivo | O que faz | Conversa com |
|---|---|---|
| `src/financas/core/dinheiro.py` | `ler_dinheiro`, `ler_taxa_percentual`, `ler_inteiro`: texto → número. `exigir_positivo` e afins: validação. `arredondar` e `arredondar_para_cima`: centavos. `formatar_reais` e `formatar_percentual`: número → texto. Define o `ErroDeValidacao`. | Usado pelos outros dois módulos; a `ui/` vai usar a leitura, e `reports/` a formatação. |
| `src/financas/core/meta_economia.py` | `calcular_meses` (RF01) e `calcular_aporte` (RF02). Devolvem `ResultadoMeses` / `ResultadoAporte`, com a tabela (`LinhaMes`: mês, aporte, rendimento, saldo). | Usa `dinheiro.py`. Vai ser lido por `reports/markdown.py` (Fase 2). |
| `src/financas/core/antecipacao.py` | `antecipar_quantidade` (RF03) e `antecipar_com_valor` (RF04). Devolvem `ResultadoAntecipacao`, com uma `LinhaAntecipacao` por parcela e os totais (`total_a_pagar`, `total_economia`, `sobra`). | Usa `dinheiro.py`. Vai ser lido por `reports/markdown.py` (Fase 2). |
| `tests/test_dinheiro.py` | Parse e formatação pt-BR, arredondamento, validação. | `dinheiro.py` |
| `tests/test_meta_economia.py` | Exemplos 6.1.a/b/c, meta inalcançável, entradas inválidas. | `meta_economia.py` |
| `tests/test_antecipacao.py` | Exemplo 6.2, q = 0, q = m, taxa 0%, valor disponível, entradas inválidas. | `antecipacao.py` |

O `tests/test_exemplo.py` da Fase 0 foi removido: os testes reais já provam que o pytest encontra o pacote.

### Como as peças se encaixam

```
digitado "10.000,00" ──ler_dinheiro──► Decimal("10000.00")
                                              │
                                     calcular_meses(meta, aporte, taxa)
                                              │
                                              ▼
                     ResultadoMeses(meses=45, tabela=(LinhaMes, ...))
                                              │
                         (Fase 2) relatório usa formatar_reais ──► "R$ 10.064,83"
```

## Como rodar

```bash
source .venv/bin/activate
pytest                                            # todos os testes
pytest --cov=financas.core --cov-report=term-missing   # cobertura linha a linha
pytest tests/test_antecipacao.py -v              # um arquivo, mostrando cada teste
```

Para experimentar as contas à mão, abra o Python dentro do venv (`python`) e digite:

```python
from decimal import Decimal
from financas.core.meta_economia import calcular_meses, calcular_aporte
from financas.core.antecipacao import antecipar_quantidade

r = calcular_meses(Decimal("10000"), Decimal("200"), Decimal("0.005"))
r.meses                 # 45
r.tabela[-1].saldo      # Decimal('10064.83...')

calcular_aporte(Decimal("10000"), 50).aporte                        # Decimal('200.00')
antecipar_quantidade(Decimal("500"), Decimal("0.02"), 10, 3).total_economia
```

## Decisões tomadas

| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| **Fórmula de antecipação = valor presente padrão**, `VP = P / (1+i)^j` | **Confirmada por você** nesta fase (é o que você usa no caderno). | Desconto simples ou tabela do credor. |
| **Limite de 1200 meses nos dois casos** (com e sem juros) e também para o prazo do RF02 | **Decidido com você.** Sem juros, uma meta de R$ 1 milhão com aporte de R$ 0,01 geraria 100 milhões de linhas e travaria o programa. | Limite só com juros, como estava no plano. |
| Saldos do exemplo 6.1.b nos testes: **R$ 9.815,75** (mês 44) e **R$ 10.064,83** (mês 45) | São os valores exatos da fórmula do plano. O plano trazia ≈ 9.821 e ≈ 10.071, aproximações um pouco diferentes. O resultado oficial (**45 meses**) não muda. | Usar os aproximados do plano (o teste falharia, porque a fórmula está certa). |
| Entrada só no formato brasileiro: **"1234.56" é recusado** com uma mensagem pedindo vírgula | Aceitar ponto como decimal tornaria "1.234" ambíguo (1234 ou 1,234?). Melhor recusar com explicação do que adivinhar. | Aceitar os dois formatos. |
| "R$" e espaços na entrada são ignorados | Assim o usuário pode colar um valor copiado de um relatório. | Recusar. |
| Na antecipação, cada linha guarda o **valor presente já arredondado** e a economia = parcela − VP arredondado | O VP é o que se paga de fato, então está em centavos. Assim cada linha fecha (VP + economia = parcela) e os totais são a soma das linhas, como pede o plano. | Arredondar a economia separadamente (raramente, poderia dar 1 centavo de diferença na linha). |
| Na meta, a tabela guarda os valores **sem arredondar** | O plano pede precisão total nos cálculos intermediários; o saldo de cada mês depende do anterior. O relatório arredonda ao mostrar. | Arredondar o rendimento todo mês, como um banco faria (muda levemente o resultado). |
| Aporte (RF02) arredondado **para cima** e a tabela é simulada com esse valor | Garante que o saldo final ≥ meta. Há teste para vários prazos. | — |
| RF04: valor disponível precisa ser **> 0** | Segue a regra do plano para valores informados (valor ≤ 0 → mensagem clara). | Aceitar 0 (resultado sempre vazio). |
| `float` recebido pelas contas gera `TypeError` | Protege a regra RNF03 (dinheiro só em `Decimal`): se algum dia um `float` escapar da interface, o erro aparece na hora, nos testes. | Converter silenciosamente. |
| Erros do usuário são `ErroDeValidacao`, com mensagem pronta em português que já cita o campo ("Valor da meta: precisa ser maior que zero.") | A interface (Fase 3) só precisa capturar esse erro e mostrar a mensagem. | Devolver códigos de erro. |
| `MetaInalcancavel` é um tipo de `ErroDeValidacao` | Para a tela é a mesma coisa: mostrar a mensagem. Os testes ainda conseguem distinguir os dois. | — |

## Termos técnicos

- **`Decimal`**: tipo numérico do Python que calcula em base 10, sem os erros de arredondamento do `float`. `Decimal("0.1") + Decimal("0.2") == Decimal("0.3")`.
- **`ROUND_HALF_UP`**: arredondamento "da escola": 0,005 vai para 0,01. **`ROUND_CEILING`**: sempre para cima (33,331 → 33,34).
- **Parse**: transformar texto em um dado estruturado ("1.234,56" → `Decimal("1234.56")`).
- **Expressão regular (regex)**: um padrão para validar texto. Em `dinheiro.py`, `_NUMERO_PT_BR` descreve "dígitos, pontos de milhar em grupos de 3, vírgula e decimais".
- **`dataclass`**: jeito curto de criar uma classe que só guarda dados (como um `struct`). Com `frozen=True` ela não pode ser alterada depois de criada, o que evita mudar um resultado sem querer.
- **`@property`**: um método que se acessa como atributo: `resultado.total_economia`, sem parênteses. Calcula o total na hora a partir das linhas.
- **Exceção (`raise`)**: forma de interromper uma função avisando que algo deu errado. Quem chamou pode capturar com `try/except` (é o que a interface vai fazer).
- **`pytest.mark.parametrize`**: roda o mesmo teste com vários valores de entrada; cada combinação conta como um teste separado.
- **`pytest.raises`**: confere que um código **lança** a exceção esperada (o teste passa quando o erro acontece).
- **Valor presente**: quanto vale hoje um dinheiro que só seria pago no futuro, descontando os juros do período.
- **Merge `--no-ff`**: junta uma branch na outra criando um commit de merge, para o histórico mostrar onde cada feature começou e terminou.

## Organização no Git

Cada módulo teve sua branch (`feat/dinheiro`, `feat/meta-economia`, `feat/antecipacao`), mesclada na branch da fase, `feat/fase-1-nucleo-calculo`. A branch da fase entra na `main` depois da sua revisão.
