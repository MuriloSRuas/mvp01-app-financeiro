# Finanças

Software desktop **offline** para tirar do caderno os cálculos financeiros do dia a dia:

- **Meta de economia** (cofrinho): em quantos meses atinjo a meta, ou quanto guardar por mês.
- **Antecipação de parcelas**: quanto economizo pagando agora as últimas parcelas de um financiamento.
- **Lançamento de gastos**: entradas e saídas, com relatório por período.

Todo cálculo gera um **relatório em Markdown** (parâmetros, fórmula, passo a passo e resultado) que pode ser salvo e aberto no Obsidian.

> Status: em desenvolvimento (MVP). Veja o andamento em [`docs/`](docs/).

## Requisitos

- Ubuntu (ou outro Linux) com **Python 3.12+**.
- Pacotes do sistema para o ambiente virtual e a interface gráfica:

  ```bash
  sudo apt install python3.12-venv python3-tk
  ```

## Instalação (desenvolvimento)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Uso

```bash
source .venv/bin/activate
python -m financas
```

## Testes

```bash
pytest                              # roda todos os testes
pytest --cov=financas.core          # mostra a cobertura do núcleo
```

## Documentação

- [`docs/arquitetura.md`](docs/arquitetura.md): como o código está organizado.
- `docs/fase-N.md`: o que foi feito em cada fase do desenvolvimento.
- [`docs/ideias-futuras.md`](docs/ideias-futuras.md): ideias anotadas para depois do MVP.

## Licença

MIT. Veja [`LICENSE`](LICENSE).
