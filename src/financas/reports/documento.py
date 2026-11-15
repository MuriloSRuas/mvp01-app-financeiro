"""Estrutura de um relatório, sem formato de saída.

Um relatório é uma lista de **blocos** (seção, parágrafo, fórmula, tabela,
passos numerados, aviso). Quem monta os blocos é `relatorios.py`; quem
decide a aparência é quem desenha:

- a **tela** (`ui/componentes.py`) desenha os blocos com fontes, cores e
  tabelas alinhadas, sem nenhum símbolo de Markdown;
- o **arquivo** (`markdown.py`) converte os mesmos blocos em Markdown,
  só quando o usuário pede para salvar.

Assim a tela e o arquivo mostram exatamente as mesmas contas.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Trecho:
    """Pedaço de texto com um estilo (normal, negrito, itálico ou código)."""

    texto: str
    negrito: bool = False
    italico: bool = False
    codigo: bool = False


Texto = tuple[Trecho, ...]


def texto(*partes: str | Trecho) -> Texto:
    """Junta partes em um texto: `texto("Total: ", negrito("R$ 10,00"))`."""
    return tuple(p if isinstance(p, Trecho) else Trecho(p) for p in partes)


def negrito(conteudo: str) -> Trecho:
    return Trecho(conteudo, negrito=True)


def italico(conteudo: str) -> Trecho:
    return Trecho(conteudo, italico=True)


def codigo(conteudo: str) -> Trecho:
    return Trecho(conteudo, codigo=True)


# --- Blocos -------------------------------------------------------------------


@dataclass(frozen=True)
class Secao:
    titulo: str


@dataclass(frozen=True)
class Paragrafo:
    conteudo: Texto


@dataclass(frozen=True)
class Formula:
    linhas: tuple[str, ...]


@dataclass(frozen=True)
class Tabela:
    cabecalhos: tuple[str, ...]
    linhas: tuple[tuple[str, ...], ...]
    # Última linha em destaque (total ou saldo final).
    destacar_ultima: bool = False


@dataclass(frozen=True)
class Passos:
    """Lista numerada: 1., 2., 3. ..."""

    itens: tuple[Texto, ...]


@dataclass(frozen=True)
class Aviso:
    conteudo: Texto


Bloco = Secao | Paragrafo | Formula | Tabela | Passos | Aviso


@dataclass
class Documento:
    titulo: str
    gerado_em: datetime
    blocos: list[Bloco] = field(default_factory=list)

    # Atalhos para montar o relatório em ordem, de cima para baixo.

    def secao(self, titulo: str) -> None:
        self.blocos.append(Secao(titulo))

    def paragrafo(self, *partes: str | Trecho) -> None:
        self.blocos.append(Paragrafo(texto(*partes)))

    def formula(self, *linhas: str) -> None:
        self.blocos.append(Formula(linhas))

    def tabela(
        self, cabecalhos: list[str], linhas: list[list[str]], destacar_ultima: bool = False
    ) -> None:
        self.blocos.append(
            Tabela(tuple(cabecalhos), tuple(tuple(l) for l in linhas), destacar_ultima)
        )

    def passos(self, itens: list[Texto]) -> None:
        self.blocos.append(Passos(tuple(itens)))

    def aviso(self, *partes: str | Trecho) -> None:
        self.blocos.append(Aviso(texto(*partes)))
