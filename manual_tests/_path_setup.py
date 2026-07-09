"""
Configuração de caminhos para scripts manuais.

Os scripts em manual_tests/ são executados a partir da raiz do projeto, mas
precisam importar módulos das pastas src/ e scripts/. Este arquivo adiciona
esses diretórios ao sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

for caminho in [SRC_DIR, SCRIPTS_DIR, PROJECT_ROOT]:
    caminho_texto = str(caminho)

    if caminho_texto not in sys.path:
        sys.path.insert(0, caminho_texto)