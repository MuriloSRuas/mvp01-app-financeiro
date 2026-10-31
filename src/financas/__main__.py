"""Ponto de entrada: permite rodar o programa com `python -m financas`.

Só abre a janela; toda a lógica fica nos outros módulos.
"""

import sys


def main() -> None:
    try:
        from financas.ui.app import main as abrir_janela
    except ModuleNotFoundError as erro:
        if erro.name in ("tkinter", "_tkinter"):
            sys.exit("O Tkinter não está instalado. No Ubuntu: sudo apt install python3-tk")
        raise
    abrir_janela()


if __name__ == "__main__":
    main()
