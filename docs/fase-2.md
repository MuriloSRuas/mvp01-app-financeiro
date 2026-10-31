# Fase 2: Relatórios

## O que foi feito

Os resultados das calculadoras agora viram **relatórios em Markdown**, prontos para a tela (Fase 3) e para o Obsidian. Todo relatório tem, nesta ordem (RF05):

1. **título** e **data/hora** em que foi gerado;
2. **dados informados**: tudo o que o usuário digitou, numa tabela;
3. **fórmula** usada, num bloco destacado;
4. **passo a passo**: cada conta intermediária e a tabela mês a mês (meta) ou parcela a parcela (antecipação);
5. **resultado** em destaque, com uma frase em linguagem simples;
6. **aviso de estimativa**.

Isso cobre a geração do texto do RF06. O salvamento em arquivo `.md`, numa pasta escolhida pelo usuário, entra na Fase 3, junto com a janela.

Os testes passaram de 85 para **124**, e a cobertura de `core/` e `reports/` está em **100%**.

## Exemplos de relatório gerado

Três exemplos reais, gerados pelo código, estão em [`docs/exemplos/`](exemplos/). Dá para abrir no Obsidian e conferir:

- [`meta-em-quantos-meses.md`](exemplos/meta-em-quantos-meses.md): RF01, exemplo 6.1.b (R$ 10.000, R$ 200/mês, 0,5% a.m. → 45 meses).
- [`meta-quanto-guardar.md`](exemplos/meta-quanto-guardar.md): RF02 (R$ 10.000 em 45 meses a 0,5% a.m. → R$ 198,72/mês).
- [`antecipacao-por-valor.md`](exemplos/antecipacao-por-valor.md): RF04 (parcelas de R$ 500 a 2% a.m., 10 restantes, R$ 1.000 disponíveis).

O texto bruto do terceiro, como fica no arquivo:

```markdown
# Antecipação de parcelas

Gerado em 31/10/2026 às 14:05.

## Dados informados

| Parâmetro | Valor |
|---|---|
| Valor da parcela (P) | R$ 500,00 |
| Juros do contrato (i) | 2% ao mês |
| Parcelas restantes, além da atual (m) | 10 |
| Valor disponível para antecipar | R$ 1.000,00 |

## Fórmula

    valor a pagar hoje = P / (1 + i)^j
    economia = P − valor a pagar hoje

`j` é o número de meses até o vencimento da parcela. Pagando hoje, você deixa de pagar os juros desses `j` meses. As **últimas** parcelas (maior `j`) são antecipadas primeiro, porque são as que mais economizam.

Com valor disponível: soma-se o valor a pagar a partir da última parcela, indo para trás, enquanto o total couber no valor.

## Passo a passo

| Vence em | Cálculo | Valor a pagar hoje | Economia |
|---|---|---|---|
| 10 meses | 500,00 / 1,02^10 | R$ 410,17 | R$ 89,83 |
| 9 meses | 500,00 / 1,02^9 | R$ 418,38 | R$ 81,62 |
| **Total** |  | **R$ 828,55** | **R$ 171,45** |

A próxima parcela (vence em 8 meses) custaria R$ 426,75 hoje e não cabe no que sobra (R$ 171,45).

## Resultado

**Pagando R$ 828,55 hoje, você economiza R$ 171,45 em juros.**

Isso quita 2 parcelas (as que venceriam em 10 e 9 meses), no lugar de pagar R$ 1.000,00 nas datas originais.

Continuam a vencer normalmente: a parcela atual (paga hoje) e as 8 que vencem de 1 a 8 meses.

Sobram R$ 171,45 do valor disponível.

> [!warning] Aviso
> Os valores são uma **estimativa** pela fórmula de valor presente. A quitação real depende do contrato e deve ser confirmada com o credor.
```

(No arquivo real, a fórmula fica num bloco ` ```text `. Aqui ela aparece recuada só porque o exemplo inteiro já está dentro de um bloco de código.)

## Mapa dos arquivos

| Arquivo | O que faz | Conversa com |
|---|---|---|
| `src/financas/reports/markdown.py` | `relatorio_meses` (RF01), `relatorio_aporte` (RF02) e `relatorio_antecipacao` (RF03/RF04): recebem o resultado do `core` e devolvem o texto Markdown. As funções com `_` no início (`_tabela`, `_secao`, `_aviso`...) são peças internas reutilizadas pelos três. | Lê os resultados de `core/meta_economia.py` e `core/antecipacao.py`; formata com `core/dinheiro.py`. A tela (Fase 3) vai mostrar e salvar esse texto. |
| `src/financas/core/dinheiro.py` | Ganhou `formatar_taxa`, que mostra a taxa como foi digitada ("0,125%"), sem arredondar. | `reports/markdown.py` |
| `tests/test_reports.py` | Confere que cada relatório tem as seções na ordem, os parâmetros, a fórmula, cada passo, o resultado e o aviso, e que o Markdown é válido (tabelas bem formadas, blocos de código fechados). | `reports/markdown.py` |
| `tests/test_dinheiro.py` | Ganhou os testes de `formatar_taxa`. | `core/dinheiro.py` |
| `docs/exemplos/*.md` | Os três relatórios de exemplo acima. | — |

## Como rodar

```bash
source .venv/bin/activate
pytest                                                        # todos os testes
pytest tests/test_reports.py -v                               # só os relatórios
pytest --cov=financas.core --cov=financas.reports --cov-report=term-missing
```

Para gerar um relatório você mesmo e ver no terminal:

```python
from decimal import Decimal
from financas.core.meta_economia import calcular_meses
from financas.reports.markdown import relatorio_meses

print(relatorio_meses(calcular_meses(Decimal("10000"), Decimal("200"), Decimal("0.005"))))
```

## Decisões tomadas

| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| A data/hora é um **parâmetro** (`gerado_em`), que por padrão é "agora" | Nos testes passamos uma data fixa, e o resultado é sempre o mesmo. | Chamar `datetime.now()` lá dentro: os testes teriam de adivinhar a hora. |
| Tabela mês a mês **completa até 24 meses**; acima disso, resumida (12 primeiros meses, o último mês de cada ano e o mês final), com aviso | O plano permite resumir prazos longos. Uma tabela de 1200 linhas no Obsidian seria ilegível. O passo a passo ainda cita o mês anterior à meta e o mês em que ela foi atingida. | Mostrar sempre tudo. |
| Aviso da **meta** adaptado: "a rentabilidade real pode variar; confirme com o banco ou a corretora" | O texto do RF05 ("quitação... confirmada com o credor") fala de dívida e não se aplica a um cofrinho. A antecipação usa o texto do RF05. | Usar a frase do credor também na meta. Se preferir outra redação, é só uma constante (`AVISO_META`). |
| Aviso no formato `> [!warning]` | No Obsidian vira um quadro amarelo de alerta (*callout*); em outros leitores de Markdown aparece como citação, que continua legível. | Texto comum ou emoji. |
| "Total de rendimentos" = saldo final exibido − total de aportes | Assim a conta fecha na tela: aportes + rendimentos = saldo final, centavo por centavo. | Somar os rendimentos mensais arredondados (poderia dar 1 ou 2 centavos de diferença). |
| Passo a passo do RF02 com **4 a 6 casas decimais** nos valores intermediários | Dá para conferir na calculadora (1,005^45 = 1,251621). O resultado final segue em centavos. | Mostrar só 2 casas (o fator 1,25 esconderia a conta). |
| No RF04, o relatório explica **por que parou** ("a próxima custaria R$ 426,75 e não cabe no que sobra") | Princípio "sem dívida cognitiva": o usuário vê o critério de parada, não só o resultado. | — |
| Taxa nos "dados informados" com `formatar_taxa` (sem arredondar) | Os dados informados precisam aparecer exatamente como foram digitados. `formatar_percentual` mostraria 0,125% como "0,13%". | Reusar `formatar_percentual`. |
| Testes conferem **trechos** do texto, não o relatório inteiro | É o que o plano pede (seção 8). Mudar uma vírgula na redação não quebra 20 testes, mas faltar um parâmetro ou o aviso quebra. | Comparar o texto completo. |

Uma ideia que surgiu e ficou para depois, anotada em `docs/ideias-futuras.md`: propriedades YAML do Obsidian (tags, tipo, data) no topo de cada relatório.

## Termos técnicos

- **Markdown**: formato de texto com marcações simples (`#` título, `**negrito**`, `|` tabela) que editores como o Obsidian exibem formatado. É o mesmo formato dos arquivos `README.md`.
- **Callout (Obsidian)**: uma citação que começa com `> [!tipo]` e o Obsidian desenha como um quadro colorido (aviso, nota, dica).
- **Bloco de código** (` ``` `): trecho exibido em fonte monoespaçada, sem formatação. Usamos para as fórmulas.
- **f-string**: texto com valores embutidos: `f"{meses} meses"` vira `"45 meses"`. Com datas, `f"{momento:%d/%m/%Y}"` formata no padrão dia/mês/ano.
- **`enumerate(lista, start=1)`**: percorre uma lista entregando também a posição (1, 2, 3...). Usado para numerar os passos.
- **Função "privada" (`_nome`)**: o `_` no início é uma convenção do Python para dizer "uso interno deste módulo, não chame de fora". O Python não proíbe, é um aviso para quem lê.
- **Teste por trecho** (`"..." in texto`): confere se um pedaço de texto aparece dentro do relatório, sem exigir que o resto seja idêntico.
