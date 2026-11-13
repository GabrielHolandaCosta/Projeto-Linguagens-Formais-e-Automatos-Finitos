"""Compila os tres documentos com pdflatex ou Tectonic no PATH."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ('relatorios/tecnico/relatorio_tecnico.tex',
             'relatorios/cliente/relatorio_cliente.tex', 'slides/apresentacao.tex')
engine = shutil.which('pdflatex') or shutil.which('tectonic')
if not engine:
    raise SystemExit('Instale TeX Live/MiKTeX com pdfLaTeX, ou Tectonic, e tente novamente.')
for document in DOCUMENTS:
    path = ROOT / document
    if Path(engine).stem.lower() == 'pdflatex':
        command = [engine, '-interaction=nonstopmode', '-halt-on-error', path.name]
        subprocess.run(command, cwd=path.parent, check=True)
        subprocess.run(command, cwd=path.parent, check=True)
    else:
        subprocess.run([engine, path.name, '--keep-logs'], cwd=path.parent, check=True)
