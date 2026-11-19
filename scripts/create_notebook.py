"""Gera notebook reprodutível sem introduzir resultados fictícios."""
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
nb=nbf.v4.new_notebook()
M=nbf.v4.new_markdown_cell; C=nbf.v4.new_code_cell
nb.cells=[
M('''# Índice de Desenvolvimento Humano Municipal no Estado do Rio de Janeiro (1991–2010)

**Rafael Sobral** · UniLaSalle · Sistemas de Informação · Prof. Alexandre Louzada · 2026.2

> **Fonte exclusiva para os resultados:** [DATA.RIO, Tabela 1727](https://www.data.rio/documents/5f39ef2738b7488bba7142b666a70f0b/about). O notebook contém código reprodutível, não valores sintéticos nem saídas inventadas.

## 1. Resumo do estudo

Três perguntas: (RQ1) evolução das médias municipais; (RQ2) desigualdades e rankings; (RQ3) associação entre IDHM inicial e ganho absoluto. São analisados apenas os anos 1991, 2000 e 2010. As estatísticas são por município e **não ponderadas por população**.'''),
M('''## 2. Contexto, método e premissas

O indicador IDHM é uma medida sintética de renda, educação e longevidade com escala de 0 a 1. Os dados são censitários (não anuais), por isso **não são interpolados**. Ausências são preservadas; a variação 1991–2010 considera apenas observações emparelhadas. Associações não implicam causalidade. O projeto registra checksum e URL do arquivo de origem.'''),
C('''from pathlib import Path
import os, sys
root = Path.cwd().resolve()
if not (root / "src").is_dir(): root = root.parent
assert (root / "src").is_dir(), "Execute este notebook dentro do projeto"
if str(root) not in sys.path:sys.path.insert(0, str(root))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display
from src.etl import RAW, run as run_etl
from src.analysis import run as run_analysis
from scripts.fetch_data import fetch
'''),
M('''## 3. Aquisição oficial e auditoria

A primeira execução faz download do Excel oficial do ArcGIS para `data/raw/` e verifica a assinatura binária. Se a URL falhar, use o download manual indicado no README. Para testes isolados, o caminho `IDHM_SOURCE_OVERRIDE` pode apontar para CSV sintético; **nunca use essa variável na entrega oficial**.'''),
C('''source = Path(os.environ.get("IDHM_SOURCE_OVERRIDE", str(RAW)))
if not source.exists():
    assert "IDHM_SOURCE_OVERRIDE" not in os.environ, "Arquivo de teste não encontrado"
    source = fetch()
print("Fonte:", source)
quality = run_etl(source)
metrics = run_analysis()
display(pd.DataFrame([quality]))'''),
M('''## 4. Tabelas processadas

A granularidade é município–ano; a tabela ampla facilita o cálculo de ganhos absolutos, sem imputação.'''),
C('''folder = root/"data/processed"
wide=pd.read_csv(folder/"idhm_wide.csv")
long=pd.read_csv(folder/"idhm_long.csv.gz")
summary=pd.read_csv(folder/"annual_summary.csv")
ranking=pd.read_csv(folder/"ranking_2010.csv")
print("Municípios:",len(wide),"| Células ausentes:",int(long.idhm.isna().sum()))
display(summary.round(3))
display(wide.head(8))'''),
M('''## 5. Resultados — RQ1: trajetória temporal

Uma média simples municipal atribui o mesmo peso a cada município, independentemente do tamanho populacional.'''),
C('''fig, ax=plt.subplots(figsize=(9,4.5))
ax.plot(summary.ano,summary.media,marker="o",label="Média",linewidth=2.4)
ax.plot(summary.ano,summary.mediana,marker="s",label="Mediana",linewidth=2.4)
ax.set(xticks=[1991,2000,2010],ylim=(0,1),ylabel="IDHM (0–1)",xlabel="Ano",title="Evolução do IDHM médio e mediano")
ax.legend();ax.grid(axis="y",alpha=.23)
plt.show()
print("Média 1991:",round(float(summary.loc[summary.ano==1991,"media"].iloc[0]),3),
      "Média 2010:",round(float(summary.loc[summary.ano==2010,"media"].iloc[0]),3))'''),
M('''## 6. Resultados — RQ2: distribuição e extremos

Boxplots comparam dispersão entre os municípios e registram possíveis valores atípicos, sem excluí-los.'''),
C('''fig,ax=plt.subplots(figsize=(9,4.5))
ax.boxplot([wide[f"idhm_{y}"].dropna().to_numpy() for y in (1991,2000,2010)],
           tick_labels=["1991","2000","2010"],patch_artist=True)
ax.set(ylabel="IDHM",ylim=(0,1),title="Dispersão do IDHM nos municípios")
ax.grid(axis="y",alpha=.2)
plt.show()
display(ranking[["municipio","idhm_2010","posicao_2010"]].head(10))
display(ranking[["municipio","idhm_2010","posicao_2010"]].tail(10))'''),
M('''## 7. Resultados — RQ3: nível inicial e mudança

O ganho é **pontos do índice**, não percentual. A correlação de Spearman é calculada apenas para municípios com ambos os anos observados. O fato de o ganho conter matematicamente o valor inicial e o teto superior de 1 exige cautela na interpretação.'''),
C('''paired=wide.dropna(subset=["idhm_1991","idhm_2010"]).copy()
paired["ganho"]=paired.idhm_2010-paired.idhm_1991
rho=paired.idhm_1991.corr(paired.ganho,method="spearman")
fig,ax=plt.subplots(figsize=(9,4.5))
ax.scatter(paired.idhm_1991,paired.ganho,alpha=.7)
ax.set(xlabel="IDHM em 1991",ylabel="Ganho absoluto 1991–2010 (pontos)",
       title=f"IDHM inicial × ganho absoluto (Spearman ρ={rho:.2f})")
ax.grid(alpha=.2)
plt.show()
print("Municípios emparelhados:",len(paired),"| Spearman:",round(float(rho),3))'''),
M('''## 8. Síntese e limitações

Os números no artigo são derivados automaticamente da planilha original por `src/analysis.py`. Compare sempre a média transversal com o ganho emparelhado, pois respondem a perguntas diferentes. O IDHM termina em 2010 nesta fonte, e observações estatísticas não bastam para determinar causalidade ou situação atual. O artigo completo pode ser regenerado por `python scripts/build_site.py`. '''),
C('''print(f"Média municipal IDHM em 2010: {float(summary.loc[summary.ano==2010,'media'].iloc[0]):.3f}")
print(f"Ganho médio 1991–2010 (municípios emparelhados): {float(paired.ganho.mean()):.3f}")
print(f"Coeficiente Spearman IDHM inicial × ganho: {rho:.3f}")
print("Fonte: DATA.RIO, Tabela 1727; cálculos próprios.")''')]
nb.metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python"}}
nbf.validate(nb)
out=ROOT/"notebooks/analise_exploratoria.ipynb"
nbf.write(nb,out)
print('Notebook:',out,'células:',len(nb.cells))
