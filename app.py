import sys
import os
from pathlib import Path

# Configura o caminho para a pasta src
BASE_DIR = Path(__file__).resolve().parent
src_path = str(BASE_DIR / 'src')
sys.path.append(src_path)

# Importa o módulo principal
try:
    from src.main import main
except ImportError as e:
    print(f"Erro ao importar: {e}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

if __name__ == "__main__":
    main()