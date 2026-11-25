import sys
from pathlib import Path

# Permite "import importar_backlog" nos testes sem empacotar a pasta scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
