"""
Configuração compartilhada para testes pytest.
Garante que os testes rodem a partir da raiz do projeto (import de config).
"""
import os
import sys

# Adiciona a raiz do projeto ao path para importar config e módulos
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
