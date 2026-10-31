# Fase 0: Preparação

## O que foi feito

Montei o "esqueleto" do projeto. Ainda não tem cálculo nem janela; tem a estrutura onde eles vão entrar e as ferramentas para testar.

- Repositório Git com `.gitignore` e uma branch só para esta fase (`chore/fase-0-preparacao`).
- Estrutura de pastas da seção 7 do plano (`src/financas/` com `core`, `reports`, `storage`, `ui`; `tests/`; `docs/`).
- `pyproject.toml` com os dados do projeto e a configuração do pytest.
- Um teste de exemplo para provar que o pytest encontra o código.
- `README.md` com instalação e uso, e `docs/arquitetura.md` explicando as camadas.

## Mapa dos arquivos

| Arquivo | O que faz | Conversa com |
|---|---|---|
| `.gitignore` | Lista o que o Git deve ignorar: o `.venv`, caches do Python, relatórios de cobertura e arquivos de banco (`*.db`, `*.sqlite3`, para nunca subir dados pessoais). | Git |
| `pyproject.toml` | "Carteira de identidade" do projeto: nome, versão, Python mínimo, dependências de desenvolvimento (`pytest`, `pytest-cov`) e configuração do pytest. É o equivalente ao `composer.json` do PHP. | `pip`, `pytest` |
| `src/financas/__init__.py` | Transforma a pasta em um **pacote** Python e guarda a versão (`0.1.0`). | Todos os módulos |
| `src/financas/__main__.py` | Executado quando você roda `python -m financas`. Por enquanto só imprime uma mensagem; na Fase 3 vai abrir a janela. | `ui/app.py` (Fase 3) |
| `src/financas/core/__init__.py` | Pacote das regras de negócio (vazio por enquanto). | `reports`, `storage`, `ui` |
| `src/financas/reports/__init__.py` | Pacote dos relatórios Markdown (vazio). | `core`, `ui` |
| `src/financas/storage/__init__.py` | Pacote do SQLite (vazio). | `core`, `ui` |
| `src/financas/ui/__init__.py` | Pacote da interface Tkinter (vazio). | todos |
| `tests/test_exemplo.py` | Teste mínimo: confirma que `financas` importa e tem a versão certa. | `financas/__init__.py` |
| `docs/arquitetura.md` | Explica as camadas e por que estão separadas. | — |
| `docs/ideias-futuras.md` | Lugar para anotar ideias fora do escopo. | — |

## Como rodar

**1. Pacotes do sistema (uma vez só).** O Ubuntu não vem com o módulo de ambiente virtual nem com o Tkinter:

```bash
sudo apt install python3.12-venv python3-tk
```

**2. Ambiente virtual e dependências (uma vez só):**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**3. No dia a dia:**

```bash
source .venv/bin/activate   # ativa o ambiente (o terminal mostra "(.venv)")
python -m financas          # roda o programa
pytest                      # roda os testes
```

Resultado esperado do `pytest`: `1 passed`.

## Decisões tomadas

| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| Layout `src/` (código em `src/financas/`) | Obriga a instalar o pacote antes de usar, então os testes testam o mesmo código que o usuário roda. | Pacote na raiz: mais simples, mas esconde erros de importação. |
| `pip install -e .` (modo editável) | Instala o pacote "apontando" para a pasta: você edita o código e a mudança vale na hora, sem reinstalar. | Ajustar `PYTHONPATH` à mão a cada terminal. |
| A raiz do repositório faz o papel da pasta `financas/` do plano | O repositório já existia (`mvp01-app-financeiro`); criar outra pasta dentro dele só adicionaria um nível. | Pasta `financas/` dentro do repositório. |
| Nomes em **português** | O plano pede um idioma só; o domínio (meta, parcela, lançamento) já é em português. | Inglês. |
| `setuptools` como ferramenta de build | É o padrão e já vem com o `pip`; não adiciona dependência de execução. | Poetry, Hatch, uv (mais uma ferramenta para aprender). |
| `pytest-cov` como dependência de desenvolvimento | O plano exige cobertura ≥ 90% no `core` (RNF07), medida com `pytest --cov`. | — |

## Termos técnicos

- **Ambiente virtual (`venv`)**: uma pasta (`.venv/`) com uma cópia isolada do Python e das bibliotecas do projeto. Evita misturar bibliotecas de projetos diferentes. Parecido com a pasta `vendor/` do Composer.
- **Pacote Python**: pasta com um arquivo `__init__.py`. Permite importar com `import financas.core`.
- **`python -m financas`**: roda o pacote como programa; o Python procura e executa o `__main__.py` dele.
- **`pyproject.toml`**: arquivo de configuração padrão de projetos Python (metadados, dependências, ferramentas).
- **Teste automatizado**: uma função que chama o código e confere o resultado com `assert`. Se a condição for falsa, o teste falha e avisa o que quebrou. Roda em segundos, sempre igual, sem você precisar clicar em nada.
- **pytest**: ferramenta que encontra e roda os testes (arquivos `test_*.py`, funções `test_*`).
- **Cobertura (coverage)**: porcentagem das linhas do código que foram executadas pelos testes. Mostra o que ficou sem teste.
- **Branch (Git)**: uma linha paralela de desenvolvimento. Cada fase/feature fica na sua branch e só entra na `main` quando estiver pronta.

## Verificação

Depois de instalar `python3.12-venv` e `python3-tk`, o `.venv` foi criado, as dependências instaladas e o `pytest` retornou `1 passed` (Python 3.12.3, pytest 9.2.0, pytest-cov 7.1.0).
