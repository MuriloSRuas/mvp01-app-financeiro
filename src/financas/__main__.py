"""Ponto de entrada: permite rodar o programa com `python -m financas`.

Por enquanto (Fase 0) só confirma que o pacote está instalado. A janela
Tkinter entra na Fase 3; este arquivo vai apenas chamá-la, para que a
lógica continue fora dele.
"""

from financas import __version__


def main() -> None:
    print(f"Finanças {__version__}: estrutura pronta. A interface chega na Fase 3.")


if __name__ == "__main__":
    main()
