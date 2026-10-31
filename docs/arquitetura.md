# Arquitetura

O Finanças é **um único programa local**: não tem servidor, API nem internet. Tudo roda no seu computador, e os dados ficam nele.

Se você vem da web, pense assim: em vez de navegador + servidor PHP + banco, temos **um só processo Python** que desenha a janela (Tkinter), faz as contas e grava num arquivo de banco (SQLite).

## As camadas

```
ui/ (Tkinter)  →  core/ (regras puras, sem UI e sem banco)
      ↓
storage/ (SQLite)  →  usa tipos do core

reports/ (Markdown)  →  transforma resultados do core em texto
```

A seta significa "conhece / importa". O `core` não conhece ninguém: ele não sabe que existe janela nem banco.

| Pasta | Responsabilidade | Pode importar | Não pode importar |
|---|---|---|---|
| `core/` | Fórmulas e regras de negócio: dinheiro, meta de economia, antecipação, totais de gastos. | Só biblioteca padrão (`decimal`, `math`, `datetime`...). | `tkinter`, `sqlite3`, `ui`, `storage`. |
| `reports/` | Monta o texto Markdown dos relatórios a partir dos resultados do `core`. A tela mostra esse mesmo texto. | `core`. | `tkinter`, `sqlite3`. |
| `storage/` | Guarda e lê os lançamentos de gastos no SQLite. Decide onde fica o arquivo do banco em cada sistema operacional. | `core`, `sqlite3`, `pathlib`. | `tkinter`, `ui`. |
| `ui/` | Janela, abas, campos e botões. Lê o que o usuário digitou, chama o `core`/`reports`/`storage` e mostra o resultado ou o erro. | Todas as outras. | (nada abaixo dela) |

### Por que separar assim?

- **Testar fica fácil.** As regras mais sensíveis (as fórmulas) estão no `core`, que é Python puro. Um teste chama a função e compara o resultado; não precisa abrir janela nem banco.
- **Trocar a interface não mexe nas contas.** Se um dia o programa virar web ou mobile, só a `ui/` muda. É o mesmo raciocínio de separar *controller* e *model* em uma aplicação web.
- **Portabilidade.** A única parte que sabe que existe Linux ou Windows é o módulo que escolhe a pasta do banco (em `storage/`). O resto usa `pathlib` e funciona igual nos dois.

## Estrutura de pastas

```
.
├── README.md
├── pyproject.toml            # metadados do projeto e config do pytest
├── docs/                     # documentação (esta pasta)
├── src/financas/
│   ├── __main__.py           # permite rodar com: python -m financas
│   ├── core/                 # regras puras
│   │   ├── dinheiro.py       # parse/formatação pt-BR, arredondamento, validação
│   │   ├── meta_economia.py  # RF01 e RF02
│   │   ├── antecipacao.py    # RF03 e RF04
│   │   └── gastos.py         # lançamento, datas, totais, saldo, ranking (RF07, RF11)
│   ├── reports/
│   │   ├── markdown.py       # monta o texto dos relatórios (RF05, RF11)
│   │   └── arquivo.py        # grava o .md em disco (RF06)
│   ├── storage/
│   │   ├── caminhos.py       # onde fica o banco em cada sistema (único código por SO)
│   │   └── repositorio.py    # SQLite: CRUD, filtro por mês, categorias
│   └── ui/
│       ├── app.py            # janela principal com abas
│       ├── componentes.py    # peças comuns às abas de cálculo
│       ├── aba_meta.py
│       └── aba_antecipacao.py
└── tests/                    # testes automatizados (pytest)
```

Três arquivos não estavam na estrutura do plano: `reports/arquivo.py` (separa "montar texto" de "gravar em disco"), `ui/componentes.py` (evita repetir nas duas abas o mesmo formulário + relatório + botão Salvar) e `storage/caminhos.py` (o "módulo isolado que decide o caminho por sistema operacional" pedido na seção 7). A aba de gastos chega na Fase 5.

## Decisões gerais

- **Dinheiro em `Decimal`, nunca `float`.** `float` guarda números em binário e erra em contas simples (`0.1 + 0.2` dá `0.30000000000000004`). `Decimal` faz contas em base 10, como no caderno.
- **No banco, valores em centavos (inteiro).** `R$ 12,34` vira `1234`. Inteiros não têm erro de arredondamento.
- **Arredondar só na hora de mostrar.** As contas internas mantêm precisão total; cada valor exibido é arredondado a 2 casas (`ROUND_HALF_UP`), e os totais somam os valores já arredondados para o relatório "fechar" visualmente.
- **Nomes em português**, em código e documentação, para manter um idioma só.
