"""Validação básica da integridade e rigor estatístico dos produtos gerados."""
from pathlib import Path
import json
import re
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"data/processed"
text=(ROOT/"docs/index.html").read_text(encoding="utf-8")
for section in ('resumo','introducao','metodologia','resultados','conclusao','fair','referencias'):
    assert f'id="{section}"' in text, f"seção ausente: {section}"
assert (ROOT/"docs/.nojekyll").exists()
assert (ROOT/"docs/assets/style.css").exists()
assert 'Rafael Sobral' in text and 'Alexandre Louzada' in text
assert (P/"metrics.json").is_file(), "Projeto final requer ETL oficial executado (não basta prévia)"
metrics=json.loads((P/"metrics.json").read_text(encoding="utf-8"))
wide=pd.read_csv(P/"idhm_wide.csv")
long=pd.read_csv(P/"idhm_long.csv.gz")
assert 60<=len(wide)<=100 and wide.municipio.is_unique
assert long.shape[0]==len(wide)*3
assert set(long.ano)=={1991,2000,2010}
assert long.idhm.dropna().between(0,1).all()
assert len(wide)==metrics["municipalities"]
for y in [1991,2000,2010]:
    m=next(x for x in metrics["annual_summary"] if int(x["ano"])==y)
    assert abs(wide[f"idhm_{y}"].mean()-m['media'])<1e-10
for chart in ['evolucao','distribuicao','ranking','convergencia']:
    assert (ROOT/f"docs/assets/{chart}.json").is_file()
    assert (ROOT/f"docs/assets/img/{chart}.png").is_file()
summary=re.search(r'<h2>Resumo</h2><p>(.*?)</p>',text,re.S)
assert summary, 'Resumo não encontrado'
words=len(re.sub(r'<[^>]+>','',summary.group(1)).split())
assert 150<=words<=250, f"Resumo {words} palavras (esperado 150–250)"
print(f"OK: artigo, FAIR, resumos, 4 gráficos, 3 anos, {len(wide)} municípios")
