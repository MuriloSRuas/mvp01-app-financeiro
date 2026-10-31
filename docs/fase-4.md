# Fase 4: Gastos (núcleo e armazenamento)

## O que foi feito

O lançamento de gastos ganhou toda a parte "por trás da tela". A aba **Gastos** na janela é a Fase 5.

1. **Regras** (`core/gastos.py`): o que é um lançamento válido (tipo, valor, data, categoria, descrição), leitura de datas `DD/MM/AAAA` e o **resumo de um período**: total de entradas, total de saídas, saldo e ranking das saídas por categoria, com percentual.
2. **Armazenamento** (`storage/`): os lançamentos ficam num arquivo **SQLite** na pasta de dados do usuário (`~/.local/share/financas/financas.db` no Ubuntu). O repositório cria, edita, exclui, lista por mês ou por período e devolve as categorias já usadas.
3. **Relatório de gastos** (`reports/markdown.py`): lançamentos do período, fórmulas, totais com a conta do saldo, ranking por categoria e resultado em linguagem simples. Pode ser salvo em `.md`, como os outros.

São **193 testes**, e a cobertura de `core/`, `reports/` e `storage/` é de **100%**.

Exemplo completo de relatório: [`docs/exemplos/relatorio-gastos.md`](exemplos/relatorio-gastos.md). O trecho principal:

```markdown
## Saídas por categoria

| #   | Categoria     | Valor       | % das saídas |
| --- | ------------- | ----------- | ------------ |
| 1   | Aluguel       | R$ 1.500,00 | 72,0%        |
| 2   | Mercado       | R$ 432,75   | 20,8%        |
| 3   | Lazer         | R$ 89,90    | 4,3%         |
| 4   | Sem categoria | R$ 60,00    | 2,9%         |

Exemplo: Aluguel = 1.500,00 / 2.082,65 = 72,0%

_Os percentuais são arredondados a uma casa; por isso a soma pode dar 99,9% ou 100,1%._

## Resultado

No período, você recebeu R$ 5.000,00 e gastou R$ 2.082,65; saldo **positivo de R$ 2.917,35**.

A categoria com mais gastos foi **Aluguel**: R$ 1.500,00 (72,0% das saídas).
```

## Mapa dos arquivos

| Arquivo | O que faz | Conversa com |
|---|---|---|
| `src/financas/core/gastos.py` | `Lancamento` (valida ao ser criado), `novo_lancamento` (limpa o texto digitado, categoria vazia → "Sem categoria"), `ler_data`/`formatar_data` e `resumir` (totais, saldo e ranking → `ResumoPeriodo`). | Usa `core/dinheiro.py`. É usado pelo repositório, pelo relatório e, na Fase 5, pela aba Gastos. |
| `src/financas/storage/repositorio.py` | `RepositorioLancamentos`: `adicionar`, `atualizar`, `excluir`, `obter`, `listar_mes`, `listar_periodo`, `categorias`. Converte `Lancamento` ↔ linha da tabela (reais ↔ centavos, `date` ↔ texto ISO). | `core/gastos.py`, módulo `sqlite3`. |
| `src/financas/storage/caminhos.py` | Decide **onde** fica o banco: Linux `~/.local/share/financas/`, Windows `%APPDATA%\financas\`. É o único arquivo que sabe qual é o sistema operacional. | Usado pela janela na Fase 5. |
| `src/financas/reports/markdown.py` | Ganhou `relatorio_gastos`. | `core/gastos.py` |
| `tests/test_gastos.py` | Lançamento válido/inválido, datas, totais, saldo negativo, ranking, empate, sem saídas, filtro do período. | `core/gastos.py` |
| `tests/test_repositorio.py` | CRUD, centavos exatos, filtro por mês (incluindo fevereiro bissexto), categorias, regras `CHECK` do banco, dados que persistem no arquivo, caminho no Linux e no Windows. | `storage/` |
| `tests/test_reports.py` | Ganhou os testes do relatório de gastos. | `reports/markdown.py` |

### Como as peças se encaixam

```
(Fase 5) tela ──novo_lancamento()──► Lancamento ──repo.adicionar()──► SQLite (centavos, data ISO)
                                                                          │
(Fase 5) "Gerar relatório" ◄── relatorio_gastos() ◄── resumir() ◄── repo.listar_periodo()
```

## Como rodar

```bash
source .venv/bin/activate
pytest                                       # 193 testes
pytest tests/test_repositorio.py -v
pytest --cov=financas.core --cov=financas.reports --cov=financas.storage --cov-report=term-missing
```

Para experimentar no terminal (banco na memória, nada é gravado):

```python
from datetime import date
from decimal import Decimal
from financas.core.gastos import novo_lancamento, resumir
from financas.storage.repositorio import RepositorioLancamentos, periodo_do_mes
from financas.reports.markdown import relatorio_gastos

repo = RepositorioLancamentos(":memory:")
repo.adicionar(novo_lancamento("entrada", Decimal("3000"), date(2026, 10, 1), "Salário"))
repo.adicionar(novo_lancamento("saida", Decimal("450.90"), date(2026, 10, 3), "Mercado"))
repo.categorias()                       # ['Mercado', 'Salário']

inicio, fim = periodo_do_mes(2026, 10)
print(relatorio_gastos(resumir(repo.listar_periodo(inicio, fim), inicio, fim)))
```

## Decisões tomadas

| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| Valor gravado em **centavos inteiros** (`valor_centavos`) | Pedido no modelo de dados do plano: o SQLite guardaria decimal como `float` e erraria centavos. Há teste ida e volta para vários valores. | Coluna `REAL`/texto. |
| Regras repetidas no banco com **`CHECK`** (tipo, valor > 0, categoria não vazia) | Se um bug pular a validação do core, o banco ainda recusa. Há testes inserindo SQL direto. | Confiar só no Python. |
| Validação dentro do `Lancamento` (`__post_init__`) | Não existe lançamento inválido em lugar nenhum do programa, nem vindo do banco. | Validar só na tela. |
| `novo_lancamento` limpa espaços e troca categoria vazia por "Sem categoria" | Regra 6.3; e "Mercado " com espaço não vira uma categoria diferente de "Mercado". | — |
| Categorias **diferenciam maiúsculas** ("mercado" ≠ "Mercado"), mas a lista aparece em ordem alfabética ignorando maiúsculas | Juntar automaticamente obrigaria o programa a escolher qual grafia manter (seria "pensar pelo usuário"). Na Fase 5 a lista de categorias existentes aparece para escolha, o que evita duplicar sem querer. | Juntar ignorando maiúsculas. |
| Período do relatório = **data inicial e final** (inclusive); `periodo_do_mes` gera o mês inteiro | O RF11 fala em "período"; o RF10 em mês. Com datas, os dois casos usam o mesmo código. | Só mês/ano. |
| Relatório de gastos **lista os lançamentos** do período | Princípio "sem dívida cognitiva": os lançamentos são os "dados informados"; sem eles não dá para conferir os totais. | Só totais e ranking. |
| Relatório de gastos **sem aviso de estimativa** | Não é previsão, é a soma do que foi lançado. O aviso do RF05 é para os cálculos. | Repetir o aviso. |
| Percentual do ranking guardado exato; arredondado a 1 casa só no relatório, com nota quando a soma pode não dar 100,0% | Regra geral do plano (arredondar só ao mostrar) + transparência sobre o efeito do arredondamento. | Ajustar percentuais para somar 100% (mudaria valores). |
| Empate no ranking → ordem alfabética | O resultado é sempre o mesmo (testável). | Ordem de inserção. |
| Barra `\|` digitada na descrição é escapada (`\|`) na tabela | Uma barra solta quebraria as colunas no Obsidian. | Remover o caractere. |
| `storage/caminhos.py` com parâmetros opcionais (`sistema`, `ambiente`, `casa`) | Permite testar o caminho do Windows rodando no Linux. Respeita `XDG_DATA_HOME`, padrão do Linux para pasta de dados. | Testar só no sistema atual. |
| Data como texto **ISO** (`2026-10-31`) no banco | Pedido no plano; a ordem alfabética do ISO é a ordem cronológica, então `BETWEEN` e `ORDER BY` funcionam direto. | Guardar `DD/MM/AAAA` (ordenaria errado). |
| Excluir/editar um id inexistente gera mensagem ("pode já ter sido excluído") | A tela mostra em vez de falhar em silêncio. | Ignorar. |

## Termos técnicos

- **SQLite**: banco de dados SQL que vive inteiro em um arquivo. Sem servidor, sem senha; vem com o Python (`import sqlite3`).
- **Repositório**: a classe que esconde o banco do resto do programa. Quem usa pede "adicione este lançamento" sem escrever SQL. Parecido com um *model*/DAO em PHP.
- **CRUD**: *Create, Read, Update, Delete*, as quatro operações básicas sobre dados.
- **Parâmetros `?` no SQL**: `execute("... WHERE id = ?", (id,))`. O valor vai separado do comando, o que impede **SQL injection**. É o mesmo que *prepared statements* do PDO no PHP.
- **Transação** (`with self._conexao:`): grupo de comandos que é gravado por inteiro (*commit*) ou desfeito por inteiro (*rollback*) se der erro.
- **`CHECK`**: regra na própria tabela; o banco recusa a linha que não obedece.
- **`:memory:`**: banco SQLite que existe só na memória e some ao fechar; ótimo para testes.
- **Fixture (pytest)**: função que prepara algo para os testes (aqui, um repositório novo) e limpa depois. O teste a recebe como parâmetro (`def test_x(repo):`).
- **`__post_init__`**: método que a `dataclass` chama logo depois de criar o objeto; usamos para validar.
- **ISO 8601**: o formato de data `AAAA-MM-DD`, padrão internacional.
- **Context manager (`with`)**: `with RepositorioLancamentos(...) as repo:` garante que o banco seja fechado ao sair do bloco, mesmo se der erro.
