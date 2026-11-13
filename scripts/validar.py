"""Valida o projeto a partir de qualquer diretorio: python scripts/validar.py."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'testes', '-v'], cwd=ROOT)
raise SystemExit(result.returncode)
