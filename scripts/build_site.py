"""Gera artigo HTML5 estático e figuras interativas a partir de métricas verificadas."""
from __future__ import annotations
import html
import os
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"
ASSETS=DOCS/"assets"
P=ROOT/"data/processed"
CONFIG=json.loads((ROOT/"config/project.json").read_text(encoding="utf-8"))
SOURCE=CONFIG["dataset_page"]

def pt(v, digits=3):
    if v is None or pd.isna(v):return "não disponível"
    return f"{float(v):.{digits}f}".replace(".", ",")

def pct(v, digits=1): return pt(v,digits) + "%"

def integer(v):return f"{int(v):,}".replace(",",".")

def safe(s):return html.escape(str(s),quote=True)

def chart_theme(fig):
    fig.update_layout(template="plotly_white",font=dict(family="Arial, sans-serif",size=13,color="#223648"),
                      paper_bgcolor="#ffffff",plot_bgcolor="#ffffff",hovermode="closest",
                      margin=dict(l=65,r=24,t=35,b=70),legend=dict(orientation="h",y=1.15,x=0),
                      colorway=["#176f6a","#e3954a","#405d9c","#a86673"])
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor="#d0dce0")
    fig.update_yaxes(gridcolor="#e7ecec",zeroline=False)
    return fig

def render_graph(fig, name, labels, *, width=950, height=495):
    ASSETS.mkdir(parents=True,exist_ok=True)
    (ASSETS/f"{name}.json").write_text(fig.to_json(),encoding="utf-8")
    return f'<div class="plot" id="{name}" role="img" aria-label="{safe(labels)}"><img src="assets/img/{name}.png" alt="{safe(labels)}"></div>'

def snapshot_figs(summary,wide,paired,ranking):
    # Figuras estáticas independentes do Plotly/Kaleido como fallback para JavaScript bloqueado.
    IMG=ASSETS/"img";IMG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":11,
                        "axes.spines.top":False,"axes.spines.right":False})
    figs={}
    years=summary.ano.to_list()
    fig=chart_theme(go.Figure())
    fig.add_trace(go.Scatter(x=years,y=summary.media,mode="lines+markers+text",text=[pt(x) for x in summary.media],textposition="top center",name="Média municipal",line=dict(width=3),marker=dict(size=10)))
    fig.add_trace(go.Scatter(x=years,y=summary.mediana,mode="lines+markers",name="Mediana",line=dict(width=3,dash="dash")))
    fig.update_layout(xaxis_title="Ano do Censo",yaxis_title="IDHM (0 a 1)")
    fig.update_yaxes(range=[0,1]);fig.update_xaxes(tickvals=years)
    figs["evolucao"]=fig
    plt.figure(figsize=(10,4.5));plt.plot(years,summary.media,marker="o",lw=3,label="Média",color="#176f6a");plt.plot(years,summary.mediana,marker="s",ls="--",label="Mediana",color="#e3954a");plt.ylim(0,1);plt.xticks(years);plt.ylabel("IDHM (0–1)");plt.legend();plt.grid(axis="y",alpha=.2);plt.tight_layout();plt.savefig(IMG/"evolucao.png",dpi=155);plt.close()

    fig=chart_theme(go.Figure())
    for year,color in zip((1991,2000,2010),("#405d9c","#e3954a","#176f6a")):
        fig.add_trace(go.Box(y=wide[f"idhm_{year}"].dropna(),name=str(year),boxpoints="outliers",marker_color=color,quartilemethod="linear",hovertemplate="IDHM: %{y:.3f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(xaxis_title="Ano do Censo",yaxis_title="Distribuição de IDHM municipal");fig.update_yaxes(range=[0,1]);figs["distribuicao"]=fig
    plt.figure(figsize=(10,4.5));vals=[wide[f"idhm_{y}"].dropna().values for y in (1991,2000,2010)];parts=plt.boxplot(vals,patch_artist=True,tick_labels=["1991","2000","2010"])
    for patch,color in zip(parts["boxes"],["#405d9c","#e3954a","#176f6a"]):patch.set_facecolor(color);patch.set_alpha(.65)
    plt.ylim(0,1);plt.ylabel("IDHM (0–1)");plt.grid(axis="y",alpha=.2);plt.tight_layout();plt.savefig(IMG/"distribuicao.png",dpi=155);plt.close()

    extremes=pd.concat([ranking.head(5),ranking.tail(5)]).drop_duplicates("municipio").sort_values("idhm_2010")
    colors=["#176f6a" if x>=ranking["idhm_2010"].quantile(.5) else "#e3954a" for x in extremes.idhm_2010]
    fig=chart_theme(go.Figure(go.Bar(x=extremes.idhm_2010,y=extremes.municipio,orientation="h",marker_color=colors,
                                     hovertemplate="%{y}: %{x:.3f}<extra></extra>")))
    fig.update_layout(xaxis_title="IDHM em 2010",yaxis_title="",margin=dict(l=180,r=30,t=15,b=55));fig.update_xaxes(range=[0,1]);figs["ranking"]=fig
    plt.figure(figsize=(10,5.3));plt.barh(extremes.municipio,extremes.idhm_2010,color=colors);plt.xlim(0,1);plt.xlabel("IDHM em 2010");plt.tight_layout();plt.savefig(IMG/"ranking.png",dpi=155);plt.close()

    fig=chart_theme(go.Figure())
    fig.add_trace(go.Scatter(x=paired.idhm_1991,y=paired.ganho,mode="markers",text=paired.municipio,
            marker=dict(size=10,color=paired.ganho,colorscale=[[0,"#d3e1e0"],[1,"#176f6a"]],line=dict(color="#ffffff",width=.75),showscale=False),
            hovertemplate="<b>%{text}</b><br>IDHM 1991: %{x:.3f}<br>Ganho: %{y:+.3f}<extra></extra>"))
    fig.update_layout(xaxis_title="IDHM em 1991",yaxis_title="Ganho absoluto 1991–2010");figs["convergencia"]=fig
    plt.figure(figsize=(10,4.5));plt.scatter(paired.idhm_1991,paired.ganho,s=30,alpha=.75,color="#176f6a");plt.xlabel("IDHM em 1991");plt.ylabel("Ganho absoluto (pontos no índice)");plt.grid(alpha=.15);plt.tight_layout();plt.savefig(IMG/"convergencia.png",dpi=155);plt.close()
    (ASSETS/"charts.js").write_text("""document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Plotly) return;
  for (const id of ['evolucao','distribuicao','ranking','convergencia']) {
    const el = document.getElementById(id); if (!el) continue;
    try {const r = await fetch('assets/'+id+'.json'); if(!r.ok) throw new Error('JSON indisponível');
      const fig=await r.json(); await Plotly.newPlot(el, fig.data, fig.layout, {responsive:true,displaylogo:false});}
    catch(err) {console.warn('Mostrando figura estática para',id,err);}
  }
});
""",encoding="utf-8")
    return figs


def shell(contents: str,meta:dict,ready:bool) -> str:
    repo_id=os.environ.get("GITHUB_REPOSITORY", "")
    link=CONFIG.get("repository_url","") or ("https://github.com/" + repo_id if repo_id else "")
    repo_button=f'<a class="button primary" href="{safe(link)}" rel="noopener noreferrer" target="_blank">Ver código no GitHub ↗</a>' if link else '<a class="button primary" href="#fair">Como reproduzir ↘</a>'
    scripts = '<script src="assets/plotly.min.js" defer></script><script src="assets/charts.js" defer></script>' if ready else ""
    version="Artigo calculado com dados oficiais" if ready else "Prévia metodológica • aguardando dados oficiais"
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="description" content="Análise acadêmica do IDHM dos municípios do Estado do Rio de Janeiro: 1991, 2000 e 2010, baseada no DATA.RIO." />
<meta name="theme-color" content="#103e48"/><title>IDHM dos municípios do Rio de Janeiro | Artigo científico</title>
<link rel="stylesheet" href="assets/style.css">{scripts}</head><body><a class="skip" href="#main">Pular para o artigo</a>
<div class="topline"><div class="container"><span>UNILASALLE • SISTEMAS DE INFORMAÇÃO</span><span>ARTIGO ACADÊMICO DIGITAL / 2026.2</span></div></div>
<header class="hero" id="top"><div class="container"><div class="eyebrow">ANÁLISE E VISUALIZAÇÃO DE DADOS EM PYTHON <span class="light-chip">1991 — 2010</span></div>
<h1>Desenvolvimento humano nos <em>municípios fluminenses</em></h1><p class="lede">Uma análise do Índice de Desenvolvimento Humano Municipal (IDHM), sua evolução histórica e desigualdades territoriais nos municípios do Estado do Rio de Janeiro.</p>
<div class="chips"><span>DATA.RIO • TABELA 1727</span><span>CIÊNCIA ABERTA / FAIR</span><span>PYTHON • PANDAS • PLOTLY</span></div>
<div class="people"><div><small>AUTORIA</small><strong>{safe(', '.join(CONFIG['authors']))}</strong></div><div><small>ORIENTAÇÃO</small><strong>{safe(CONFIG['professor'])}</strong></div><div><small>INSTITUIÇÃO</small><strong>{safe(CONFIG['institution'])} · {safe(CONFIG['course'])}</strong></div></div>
<div class="hero-actions">{repo_button}<a class="button outline" href="#resultados">Explorar resultados ↓</a></div></div></header>
<nav class="nav"><div class="container">{''.join(f'<a href="#{x}">{y}</a>' for x,y in [('resumo','Resumo'),('introducao','Introdução'),('metodologia','Metodologia'),('resultados','Resultados'),('conclusao','Conclusão'),('fair','Dados e FAIR'),('referencias','Referências')])}</div></nav>
<main id="main"><div class="container"><p class="status" aria-live="polite">{version}</p>{contents}</div></main>
<footer><div class="container"><span>Rafael Sobral • UniLaSalle • 2026</span><a href="#top">Voltar ao topo ↑</a></div></footer></body></html>'''


def cards(items):
    return '<div class="metrics">'+''.join(f'<div class="metric"><div class="metric-value">{safe(val)}</div><div class="metric-name">{safe(lbl)}</div></div>' for val,lbl in items)+'</div>'

def questions():
    return '<div class="questions"><div><b>RQ1</b><span>Qual foi a evolução média do IDHM municipal entre 1991, 2000 e 2010?</span></div><div><b>RQ2</b><span>Como se distribuem os níveis de IDHM e quais municípios apresentaram maiores e menores valores em 2010?</span></div><div><b>RQ3</b><span>Municípios com IDHM inicial menor apresentaram maiores ganhos absolutos até 2010?</span></div></div>'

def source_block():
    return f'''<section id="fair" class="section"><div class="section-label">05 / ACESSO E REPRODUTIBILIDADE</div><h2>5. Disponibilidade dos dados e declaração FAIR</h2>
<p>Os dados brutos procedem da publicação da Prefeitura da Cidade do Rio de Janeiro, disponibilizada no catálogo <a href="{safe(SOURCE)}">DATA.RIO</a>. O script registra endereço de origem, data de aquisição e checksum SHA-256. O repositório armazena o Excel bruto, a cópia normalizada e as tabelas de resultados após o primeiro processamento.</p>
<div class="fair-grid"><div><b>F · Findable</b><p>README, autoria e referência persistente ao item do DATA.RIO.</p></div><div><b>A · Accessible</b><p>Repositório público, publicação em GitHub Pages e fonte acessível por URL aberta.</p></div><div><b>I · Interoperable</b><p>CSV/GZ, JSON e <code>data/data_dictionary.md</code> documentando tipos e variáveis.</p></div><div><b>R · Reusable</b><p>Licença de software MIT, atribuição dos dados CC BY 4.0 e dependências versionadas.</p></div></div>
<p>Reproduza os resultados em ambiente Python 3.11/3.12, a partir do diretório do projeto:</p><pre><code>git clone &lt;URL-DO-REPOSITORIO&gt;
cd projeto-idhm-rj
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_all.py</code></pre><p>Os arquivos processados são derivados integralmente da fonte original, sem interpolação ou substituição dos dados faltantes. A configuração e a forma de obtenção do Excel estão documentadas no repositório.</p></section>
<section id="referencias" class="section"><div class="section-label">06 / BASES E REFERÊNCIAS</div><h2>6. Referências</h2>
<ol class="refs"><li>PREFEITURA DA CIDADE DO RIO DE JANEIRO. <i>Índice de Desenvolvimento Humano (IDH), por ordem decrescente, dos Municípios do Estado do Rio de Janeiro em 1991/2000/2010</i>. DATA.RIO, Tabela 1727. Disponível em: <a href="{safe(SOURCE)}">Data.Rio</a>. Acesso em: 19 nov. 2026.</li>
<li>PROGRAMA DAS NAÇÕES UNIDAS PARA O DESENVOLVIMENTO (PNUD); IPEA; FUNDAÇÃO JOÃO PINHEIRO. <i>Atlas do Desenvolvimento Humano no Brasil</i>. Disponível em: <a href="https://www.atlasbrasil.org.br/">Atlas Brasil</a>. Acesso em: 19 nov. 2026.</li>
<li>THE PANDAS DEVELOPMENT TEAM. <i>pandas: Python Data Analysis Library</i>. Disponível em: <a href="https://pandas.pydata.org/">pandas.pydata.org</a>. Acesso em: 19 nov. 2026.</li>
<li>PLOTLY TECHNOLOGIES INC. <i>Plotly Python Open Source Graphing Library</i>. Disponível em: <a href="https://plotly.com/python/">plotly.com/python</a>. Acesso em: 19 nov. 2026.</li>
<li>WILKINSON, M. D. et al. The FAIR Guiding Principles for scientific data management and stewardship. <i>Scientific Data</i>, v. 3, 160018, 2016. DOI: <a href="https://doi.org/10.1038/sdata.2016.18">10.1038/sdata.2016.18</a>.</li></ol></section>'''


def core_method(n, missing):
    return f'''<section id="introducao" class="section"><div class="section-label">01 / QUESTÕES DE PESQUISA</div><h2>1. Introdução</h2>
<p>O Índice de Desenvolvimento Humano Municipal (IDHM) resume três dimensões do desenvolvimento: longevidade, educação e renda. O indicador é apresentado em escala de 0 a 1 e permite analisar diferenças entre municípios, embora não substitua indicadores específicos de distribuição de renda, infraestrutura ou condições de vida. O DATA.RIO disponibiliza uma tabela histórica para 1991, 2000 e 2010 que permite investigar tendências e heterogeneidade territorial [1–2].</p>
<p>O objetivo do trabalho é descrever a evolução, a dispersão e a posição relativa dos municípios fluminenses, com atenção a três perguntas de pesquisa:</p>{questions()}
<p>A análise é observacional, restrita aos anos presentes na fonte. Nenhuma correlação será interpretada como relação de causa e efeito.</p></section>
<section id="metodologia" class="section"><div class="section-label">02 / RASTREABILIDADE</div><h2>2. Metodologia e pipeline de dados</h2>
<h3>2.1. Fonte e unidade de análise</h3><p>A fonte primária é a Tabela 1727 do DATA.RIO: <i>Índice de Desenvolvimento Humano (IDH), por ordem decrescente, dos Municípios do Estado do Rio de Janeiro em 1991/2000/2010</i> [1]. O registro analítico é o par município–ano. O processamento preserva a planilha original e converte seus valores para uma tabela longa de dados.</p>
<h3>2.2. Extração, limpeza e validação</h3><p>O programa baixa o arquivo original, registra sua assinatura SHA-256, lê as abas da planilha e identifica as colunas de município e IDHM para os três anos. Campos numéricos usam conversão explícita de vírgula decimal; municípios são normalizados apenas para auditoria de duplicidade. Valores ausentes são mantidos como nulos e <b>não são imputados</b>. Registros suspeitos ou layouts incompatíveis interrompem o processamento com diagnóstico, evitando conversões silenciosas.</p>
<div class="pipeline"><span>Excel do DATA.RIO</span><span>Detecção de cabeçalhos</span><span>Validação e tipos</span><span>CSV.GZ / JSON</span><span>Gráficos / HTML</span></div>
<h3>2.3. Estatísticas e critérios</h3><p>A RQ1 apresenta média e mediana simples dos IDHMs disponíveis para cada ano e a média dos ganhos emparelhados dos municípios com valores válidos em 1991 e 2010. A RQ2 compara os extremos de 2010 e a distribuição municipal (amplitude, quartis e dispersão). A RQ3 utiliza a correlação de Spearman entre IDHM inicial e ganho absoluto, calculada apenas para municípios presentes nos dois períodos. A unidade de análise é sempre o <b>município, sem ponderação populacional</b>.</p>
<h3>2.4. Trecho exemplificativo do código Python</h3><pre><code>long = wide.melt(
    id_vars=["municipio"],
    value_vars=["idhm_1991", "idhm_2000", "idhm_2010"],
    var_name="ano", value_name="idhm"
)

paired = wide.dropna(subset=["idhm_1991", "idhm_2010"])
paired["ganho"] = paired.idhm_2010 - paired.idhm_1991
rho = paired.idhm_1991.corr(paired.ganho, method="spearman")</code></pre>
<p class="small-note">Os scripts <code>src/etl.py</code>, <code>src/analysis.py</code> e <code>scripts/build_site.py</code> documentam o processamento completo. Após a aquisição do arquivo original, a validação resultou em {safe(n)} municípios e {safe(missing)} células de IDHM ausentes nas três datas{'' if isinstance(n,int) else ' (dados aguardando execução)'}.</p></section>'''


def build_ready(metrics):
    summary=pd.read_csv(P/"annual_summary.csv")
    wide=pd.read_csv(P/"idhm_wide.csv")
    paired=wide.dropna(subset=["idhm_1991","idhm_2010"]).copy();paired["ganho"]=paired.idhm_2010-paired.idhm_1991
    ranking=pd.read_csv(P/"ranking_2010.csv")
    figs=snapshot_figs(summary,wide,paired,ranking)
    m={int(row["ano"]):row for row in metrics["annual_summary"]}
    n=metrics["municipalities"]
    delta=metrics["mean_paired_gain"]
    rho=metrics["corr_spearman_baseline_gain"]
    missing=json.loads((P/"quality_report.json").read_text(encoding="utf-8"))["observacoes_ausentes"]
    years="; ".join(f"{yr}: {pt(m[yr]['media'])}" for yr in (1991,2000,2010))
    abstract=f'''Este estudo examina a evolução do Índice de Desenvolvimento Humano Municipal (IDHM) nos municípios do Estado do Rio de Janeiro nos anos censitários de 1991, 2000 e 2010, utilizando a Tabela 1727 do portal DATA.RIO. O objetivo é descrever mudanças temporais, diferenças territoriais e a associação entre nível inicial de desenvolvimento e ganho posterior. Desenvolveu-se um pipeline reprodutível em Python para obtenção da planilha Excel original, registro de proveniência, identificação de cabeçalhos, padronização de campos, auditoria de dados faltantes e exportação de arquivos CSV e JSON. Foram aplicadas estatísticas descritivas, comparação emparelhada, distribuição por município, visualizações interativas e correlação de Spearman. O processamento identificou {n} municípios, com médias simples de IDHM de {pt(m[1991]['media'])} em 1991, {pt(m[2000]['media'])} em 2000 e {pt(m[2010]['media'])} em 2010. Entre os {metrics['paired_municipalities']} municípios com observações nos extremos do período, o ganho médio foi de {pt(delta)} ponto no índice. A associação entre IDHM inicial e ganho absoluto apresentou coeficiente de Spearman de {pt(rho,2)}. Os achados mostram mudanças no indicador e heterogeneidade entre territórios, sem inferência causal. A análise é limitada à cobertura e à periodicidade da planilha histórica, não devendo ser interpretada como descrição da situação atual. Código, arquivos derivados e instruções de reprodução são disponibilizados segundo princípios FAIR.'''
    assert 150 <= len(abstract.split()) <= 250, len(abstract.split())
    score='negativa' if rho is not None and rho<0 else ('positiva' if rho is not None and rho>0 else 'nula')
    top=metrics["top5_2010"][0];bottom=metrics["bottom5_2010"][0]
    tabrows=''.join(f'<tr><th>{x}</th><td>{m[x]["n"]}</td><td>{pt(m[x]["media"])}</td><td>{pt(m[x]["mediana"])}</td><td>{pt(m[x]["desvio_padrao"])}</td><td>{pt(m[x]["amplitude_p90_p10"])}</td></tr>' for x in (1991,2000,2010))
    contents=f'''<section class="section summary"><div class="section-label">INDICADORES • HISTÓRICO / 1991–2010</div>{cards([(integer(n),'Municípios processados'),(pt(m[2010]['media']),'Média municipal em 2010'),('+'+pt(delta),'Ganho médio emparelhado 1991–2010'),(pt(rho,2),'Spearman: IDHM inicial × ganho')])}</section>
<section id="resumo" class="section"><div class="section-label">RESUMO / ABSTRACT</div><h2>Resumo</h2><p>{abstract}</p><p><b>Palavras-chave:</b> IDHM; municípios fluminenses; desigualdade territorial; análise exploratória; Python; ciência aberta.</p>
<div class="abstract-en"><h3>Abstract</h3><p>This observational study examines Municipal Human Development Index (MHDI) data for municipalities in the State of Rio de Janeiro in 1991, 2000, and 2010, based on Table 1727 from the official DATA.RIO portal. A reproducible Python pipeline downloads the original spreadsheet, records provenance, validates and normalizes the tabular data, preserves missing values, and exports machine-readable outputs. The analysis investigates temporal trends, territorial inequality, and the association between initial MHDI and subsequent absolute gains. The dataset contains {n} municipalities; the 2010 unweighted mean MHDI was {m[2010]['media']:.3f}. Among {metrics['paired_municipalities']} municipalities with paired endpoint observations, the average absolute gain was {delta:.3f}; Spearman correlation between 1991 MHDI and gain was {rho:.2f}. Descriptive statistics, interactive charts, and reproducibility instructions are provided. Municipal observations receive equal statistical weight rather than population weights. Missing observations remain null, and comparisons of absolute change use only municipalities with available endpoint values. The original data and all transformations are documented for independent validation and reuse. The analysis does not establish causality, and the historical data do not describe current development conditions.</p><p><b>Keywords:</b> MHDI; Rio de Janeiro municipalities; territorial inequality; exploratory data analysis; Python; open science.</p></div></section>
{core_method(n,missing)}
<section id="resultados" class="section"><div class="section-label">03 / RESULTADOS EMPÍRICOS</div><h2>3. Resultados e discussão</h2>
<div class="rq">RQ1 · EVOLUÇÃO NO TEMPO</div><h3>O IDHM médio aumentou entre os três anos observados</h3>
<p>As médias aritméticas municipais foram <b>{years}</b>. Entre {metrics['paired_municipalities']} municípios com informação em 1991 e 2010, o ganho médio emparelhado foi <b>{pt(delta)} ponto no índice</b> (mediana {pt(metrics['median_paired_gain'])}). A comparação emparelhada evita confundir mudanças com inclusão ou exclusão de municípios devido a valores faltantes.</p>
<figure>{render_graph(figs['evolucao'],'evolucao','Média e mediana de IDHM municipal em 1991, 2000 e 2010')}<figcaption>Figura 1 — Média e mediana municipal, sem ponderação populacional. Fonte: DATA.RIO, Tabela 1727; elaboração própria.</figcaption></figure>
<div class="table-scroll"><table><caption>Quadro 1 — Estatísticas descritivas por ano</caption><thead><tr><th>Ano</th><th>Municípios válidos</th><th>Média</th><th>Mediana</th><th>Desvio padrão</th><th>P90 − P10</th></tr></thead><tbody>{tabrows}</tbody></table></div>
<div class="rq">RQ2 · DISPARIDADES MUNICIPAIS</div><h3>Diferenças entre municípios permanecem observáveis em 2010</h3>
<p>O maior IDHM em 2010, na amostra analisada, foi observado em <b>{safe(top['municipio'])} ({pt(top['idhm_2010'])})</b>; o menor foi registrado em <b>{safe(bottom['municipio'])} ({pt(bottom['idhm_2010'])})</b>. A diferença entre os extremos foi de <b>{pt(top['idhm_2010']-bottom['idhm_2010'])} ponto</b>. Rankings descrevem a ordem na base, mas isoladamente não determinam causas ou necessidade relativa de políticas públicas.</p>
<figure>{render_graph(figs['ranking'],'ranking','Cinco maiores e cinco menores valores de IDHM em 2010')}<figcaption>Figura 2 — Cinco maiores e cinco menores IDHMs em 2010. Fonte: DATA.RIO, Tabela 1727; elaboração própria.</figcaption></figure>
<p>O desvio padrão dos IDHMs municipais foi de <b>{pt(m[1991]['desvio_padrao'])}</b> em 1991 e <b>{pt(m[2010]['desvio_padrao'])}</b> em 2010. A comparação das distribuições mostra dispersão entre localidades em vez de apenas uma média agregada.</p>
<figure>{render_graph(figs['distribuicao'],'distribuicao','Boxplots da distribuição de IDHM por município em 1991, 2000, 2010')}<figcaption>Figura 3 — Distribuição do IDHM entre municípios em cada ano censitário. Fonte: DATA.RIO, Tabela 1727; elaboração própria.</figcaption></figure>
<div class="rq">RQ3 · GANHO E NÍVEL INICIAL</div><h3>Relação entre desenvolvimento inicial e variação subsequente</h3>
<p>A correlação de Spearman entre IDHM de 1991 e ganho absoluto até 2010 foi <b>ρ = {pt(rho,2)}</b>, indicando associação de sinal <b>{score}</b> nos {metrics['paired_municipalities']} municípios com dados emparelhados. O ganho absoluto é a diferença entre os dois valores do índice, e não uma variação percentual. Mesmo diante de associação, efeitos de teto, dependência matemática entre nível inicial e mudança e outros fatores impedem interpretação causal.</p>
<figure>{render_graph(figs['convergencia'],'convergencia','Dispersão do IDHM 1991 versus ganho absoluto de IDHM até 2010')}<figcaption>Figura 4 — IDHM inicial e ganho absoluto entre 1991 e 2010. Cada ponto representa um município. Fonte: DATA.RIO, Tabela 1727; elaboração própria.</figcaption></figure>
<p>As correlações são análises exploratórias e não devem ser interpretadas como convergência socioeconômica estabelecida; também seria necessário controlar a configuração territorial e mudanças metodológicas ao longo do período.</p></section>
<section id="conclusao" class="section"><div class="section-label">04 / SÍNTESE</div><h2>4. Conclusão</h2><p>O estudo identificou aumento da média municipal do IDHM entre 1991 e 2010 no conjunto extraído do DATA.RIO. A média passou de <b>{pt(m[1991]['media'])}</b> para <b>{pt(m[2010]['media'])}</b>, enquanto o ganho médio emparelhado foi de <b>{pt(delta)} ponto</b>. Persistiram diferenças entre os municípios, evidenciadas pelos extremos e pela dispersão dos valores de 2010. A associação estimada entre situação inicial e ganho absoluto foi de <b>ρ = {pt(rho,2)}</b>, sem justificar conclusões causais.</p>
<p>Como limitações, destacam-se a defasagem histórica (último ano 2010), a ausência de ponderação populacional, a dependência dos dados publicados e o fato de o IDHM sintetizar dimensões heterogêneas. Pesquisas futuras podem incorporar componentes específicos de renda, educação e longevidade, acompanhar períodos posteriores e explorar a distribuição intramunicipal.</p></section>{source_block()}'''
    (DOCS/"index.html").write_text(shell(contents,metrics,True),encoding="utf-8")
    print(f"Artigo gerado com dados de {n} municípios")


def build_pending():
    abstract='''Esta pesquisa apresenta um protocolo de análise do Índice de Desenvolvimento Humano Municipal (IDHM) para os municípios do Estado do Rio de Janeiro nos anos de 1991, 2000 e 2010, utilizando a Tabela 1727 do portal público DATA.RIO. O objetivo é avaliar a evolução temporal do indicador, comparar diferenças entre municípios e investigar a associação entre o IDHM inicial e a mudança posterior. O projeto estabelece um pipeline reprodutível em Python para obtenção do arquivo Excel original, identificação dos campos tabulares, normalização de números e nomes de municípios, verificação de ausências e duplicidades e exportação de arquivos abertos. As análises previstas incluem média, mediana, medidas de dispersão, rankings municipais e correlação de Spearman, apresentadas em gráficos interativos no artigo HTML final. O material disponível antes da execução é uma prévia metodológica: não contém resultados numéricos da planilha, pois a extração da fonte oficial ainda não foi concluída. Depois de executado, o pipeline substitui automaticamente esta prévia por resultados efetivamente calculados, preservando dados brutos e registros de proveniência. As limitações incluem a periodicidade censitária, a defasagem do último ano observado e a impossibilidade de inferir relações causais por meio de estatísticas descritivas. O trabalho adota princípios FAIR para reprodução e reuso.'''
    assert 150<=len(abstract.split())<=250
    contents=f'''<section id="resumo" class="section"><div class="section-label">RESUMO • PRÉVIA METODOLÓGICA</div><h2>Resumo</h2><p>{abstract}</p><p><b>Palavras-chave:</b> IDHM; municípios fluminenses; dados abertos; análise exploratória; Python; ciência aberta.</p></section>
{core_method('a calcular', 'a calcular')}
<section id="resultados" class="section"><div class="section-label">03 / RESULTADOS</div><h2>3. Resultados e discussão</h2><div class="pending"><b>Resultados aguardando processamento da planilha oficial.</b><p>Não foram inseridos números de outras bases nem resultados estimados. Execute <code>python scripts/build_all.py</code> ou publique pelo workflow do GitHub Actions para gerar automaticamente médias, rankings, visualizações e discussão baseados na Tabela 1727.</p></div></section>
<section id="conclusao" class="section"><div class="section-label">04 / CONCLUSÃO</div><h2>4. Conclusão</h2><p>A conclusão empírica será gerada somente após validação e cálculo dos resultados da planilha DATA.RIO; a ausência momentânea de indicadores impede afirmar a direção ou a magnitude das variações de IDHM.</p></section>{source_block()}'''
    (DOCS/"index.html").write_text(shell(contents,{},False),encoding="utf-8")
    print("Prévia acadêmica sem números gerada; execute após obter Excel para artigo definitivo")

if __name__=="__main__":
    if (P/"metrics.json").exists():
        build_ready(json.loads((P/"metrics.json").read_text(encoding="utf-8")))
    else:build_pending()
