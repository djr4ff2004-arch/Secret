#!/usr/bin/env python3
"""
Ferramenta de Exploração Android - Ponto de Entrada
Gera arquivos MP4 maliciosos com payload injetado para exploração de vulnerabilidades Android
"""

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli_interface import ExploitCLI


def main():
    """Ponto de entrada principal"""
    
    cli = ExploitCLI()
    cli.run()


if __name__ == "__main__":
    main()
