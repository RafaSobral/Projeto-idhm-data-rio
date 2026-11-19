"""Ponto de entrada executável: Excel oficial → ETL → EDA → artigo HTML."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--skip-download", action="store_true")
    p.add_argument("--source", type=Path)
    a=p.parse_args()
    source=a.source
    if not a.skip_download and not source:
        subprocess.run([sys.executable,str(ROOT/"scripts/fetch_data.py")],check=True,cwd=ROOT)
    if source is None: source=ROOT/"data/raw/idhm_municipios_rj_1991_2000_2010.xls"
    subprocess.run([sys.executable,"-m","src.etl","--source",str(source)],check=True,cwd=ROOT)
    subprocess.run([sys.executable,"-m","src.analysis"],check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/"scripts/build_site.py")],check=True,cwd=ROOT)

if __name__=="__main__":main()
