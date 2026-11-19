# IDHM dos municípios do Estado do Rio de Janeiro (1991–2010)

**Artigo científico e projeto de análise de dados com Python — UniLaSalle, Sistemas de Informação, 6º período (2026.2).**

**Autor:** Rafael Sobral  
**Professor orientador:** Alexandre Louzada  
**Disciplina:** Linguagem de Programação — Análise e Visualização de Dados com Python

**Palavras-chave:** IDHM; Rio de Janeiro; análise exploratória; municípios; indicadores sociais; Python; ciência aberta; FAIR.

## 1. Resumo executivo

Este projeto estuda o **Índice de Desenvolvimento Humano Municipal (IDHM)** nos municípios do Estado do Rio de Janeiro nos anos **1991, 2000 e 2010**. A fonte primária é a tabela oficial **1727** do [DATA.RIO](https://www.data.rio/documents/5f39ef2738b7488bba7142b666a70f0b/about), publicada pela Prefeitura da Cidade do Rio de Janeiro. O pipeline em Python baixa a planilha Excel original, preserva os dados brutos, valida a estrutura das colunas, mantém os valores ausentes e produz bases normalizadas, estatísticas descritivas, rankings municipais, gráficos e artigo web em HTML.

> **Atenção ao estado inicial:** O ZIP contém uma **prévia metodológica** em `docs/index.html`, mas ainda **não contém as estatísticas calculadas da planilha oficial**. No ambiente usado para preparar o projeto, o download do arquivo binário XLS foi bloqueado. **Na primeira execução local com internet ou pelo GitHub Actions, o script baixa a fonte, calcula os valores e substitui automaticamente a prévia pelo artigo científico com os resultados e quatro gráficos.** Nenhum valor de IDHM foi inventado ou substituído por números de outra fonte.

## 2. Perguntas de pesquisa

1. **RQ1:** Qual foi a evolução média do IDHM municipal entre 1991, 2000 e 2010?
2. **RQ2:** Como se distribuem os níveis de IDHM e quais municípios apresentaram maiores e menores valores em 2010?
3. **RQ3:** Municípios com IDHM inicial menor apresentaram maiores ganhos absolutos até 2010?

## 3. Fonte original e licença

**Título:** Índice de Desenvolvimento Humano (IDH), por ordem decrescente, dos Municípios do Estado do Rio de Janeiro em 1991/2000/2010.

**Publicador:** Prefeitura da Cidade do Rio de Janeiro / DATA.RIO.  
**Identificador do catálogo ArcGIS:** `5f39ef2738b7488bba7142b666a70f0b`.  
**Página perene da fonte:** https://www.data.rio/documents/5f39ef2738b7488bba7142b666a70f0b/about  
**Download direto do Excel original:** https://www.arcgis.com/sharing/rest/content/items/5f39ef2738b7488bba7142b666a70f0b/data  
**Licença declarada no catálogo:** CC BY 4.0.  
**Período dos dados:** 1991, 2000, 2010. A atualização recente do arquivo no portal não torna os dados contemporâneos.

> O IDHM é um índice entre 0 e 1. As médias são **não ponderadas por população**, e variações absolutas são expressas em **pontos do índice**. Correlações não representam causalidade.

## 4. Arquivos do projeto

```text
projeto_idhm_rj/
├── .github/workflows/publish.yml     # CI: coleta o Excel, processa e publica Pages
├── .gitignore
├── README.md
├── LICENSE                         # Código MIT
├── CONTENT_LICENSE.md               # Licenças dos dados/texto/figuras
├── THIRD_PARTY_NOTICES.md
├── requirements.txt                 # Dependências com versões congeladas
├── config/project.json             # Autores, professor, URL do GitHub
├── data/
│   ├── raw/                         # Excel original e metadados de proveniência após execução
│   ├── processed/                   # CSV, CSV.GZ e JSON após execução
│   └── data_dictionary.md           # Significado e tipos de cada variável
├── notebooks/
│   └── analise_exploratoria.ipynb   # Notebook de exploração e validação
├── src/
│   ├── __init__.py
│   ├── etl.py                       # Leitura estruturada e limpeza
│   └── analysis.py                  # Estatísticas e comparações
├── scripts/
│   ├── fetch_data.py                # Download auditável do Excel oficial
│   ├── build_all.py                 # Orquestração de ponta a ponta
│   ├── build_site.py                # Artigo e quatro gráficos Plotly/PNG
│   └── validate_project.py          # Validação da entrega final
├── tests/test_etl.py               # Testes com dados sintéticos (não resultados de pesquisa)
└── docs/
    ├── .nojekyll                    # Publicação HTML sem processar Jekyll
    ├── index.html                   # Artigo final após primeira execução
    └── assets/                     # CSS, biblioteca Plotly, gráficos gerados
```

## 5. Execução local

Instale o **Python 3.11 ou 3.12**. Em um terminal na raiz do projeto:

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_all.py
python scripts/validate_project.py
```

A primeira linha `build_all.py` baixa o Excel do ArcGIS, valida a assinatura de arquivo e registra `data/raw/source_provenance.json` com SHA-256. Em seguida, são criados:

- `data/processed/idhm_wide.csv`, `idhm_long.csv.gz`, `annual_summary.csv`, `ranking_2010.csv`, `variacao_municipios.csv`, `metrics.json` e `quality_report.json`;
- `docs/index.html` com os resultados fundamentados na tabela 1727;
- quatro figuras interativas (Plotly) e seus fallbacks PNG, preservados em `docs/assets/`.

Para executar sem acesso de rede, faça download manual do Excel na página oficial e salve-o em `data/raw/idhm_municipios_rj_1991_2000_2010.xls`. Em seguida, use:

```bash
python scripts/build_all.py --skip-download
```

Se o site da fonte estiver indisponível, o projeto **falhará explicitamente**; os códigos não fabricarão observações. Se o layout do Excel mudar, o ETL encerrará com diagnóstico de leitura e de aba em vez de aceitar registros incorretos. É possível testar as heurísticas com a suíte sintética:

```bash
python -m pytest -q
```

## 6. GitHub Pages — publicação sem Jekyll

1. Crie repositório **público**, por exemplo `projeto-idhm-rj`.
2. Extraia o ZIP e envie **todos os arquivos dentro de `projeto_idhm_rj/` à raiz do repositório**, inclusive a pasta oculta `.github/` com `publish.yml`.
3. No GitHub, vá a **Settings → Pages → Build and deployment** e selecione **GitHub Actions**, **não** `Deploy from a branch /docs`.
4. Na aba **Actions**, abra **Processar IDHM DATA.RIO e publicar artigo** e execute **Run workflow** (ou envie um novo commit para `main`).
5. O job obtém a fonte oficial, roda ETL/EDA, atualiza `docs/` e as tabelas, valida o HTML e publica. A primeira execução pode necessitar de aprovação de Actions/Pages nas configurações do repositório.
6. Compartilhe os dois links: repositório `https://github.com/USUARIO/projeto-idhm-rj` e artigo `https://USUARIO.github.io/projeto-idhm-rj/`.

> Para corrigir o problema antigo de **`No such file or directory /github/workspace/docs`**, confirme que a pasta `docs/` está na raiz. A publicação aqui é por workflow com `actions/deploy-pages`, e `docs/.nojekyll` impede processamento Jekyll desnecessário.

**Caso o workflow não consiga fazer commit:** em **Settings → Actions → General → Workflow permissions**, verifique se **Read and write permissions** estão disponíveis. O token do workflow solicita `contents: write`, mas políticas de organização podem restringir a gravação. A etapa de publicação usa `pages: write` e `id-token: write`.

## 7. Metodologia e controle de qualidade

- **Entrada:** arquivo bruto Excel preservado; SHA-256 documentado.
- **Parsing:** identificação das colunas por padrões, formatos decimais e consistência das linhas de municípios.
- **Rejeição:** layouts incompatíveis, leituras ambíguas e municípios duplicados geram falha explícita. Não se fazem exclusões silenciosas.
- **Valores faltantes:** preservados como nulos na tabela longa; comparação emparelhada usa apenas registros válidos em ambos os anos.
- **Indicadores:** média e mediana simples, desvio padrão, quantis, extremos, ganhos absolutos, rankings e correlação de Spearman.
- **Gráficos:** (1) evolução média/mediana, (2) extremos municipais em 2010, (3) distribuição por ano, (4) dispersão entre nível inicial e ganho.
- **Limitações:** resultados não são atualizados para 2026; dados de 1991 a 2010, ausência de ponderação populacional, heterogeneidade municipal, possíveis mudanças metodológicas, associação não causal.

## 8. Princípios FAIR

| Pilar | Implementação |
|---|---|
| **Findable** | README com autores, pergunta e link permanente da fonte; dicionário de dados e nomes indexáveis |
| **Accessible** | GitHub público, código sem autenticação paga, publicação em GitHub Pages, URL oficial de aquisição |
| **Interoperable** | CSV, CSV.GZ, JSON, dicionário de variáveis, codificação UTF-8 e tipos explícitos |
| **Reusable** | MIT para software, CC BY 4.0 para texto/figuras próprios, atribuição ao DATA.RIO, requirements.txt fixado e instruções de execução |

## 9. Declaração de integridade

Os arquivos da primeira versão do projeto sobre **Gapminder** não são utilizados nem são fonte da análise. As saídas deste repositório são **geradas exclusivamente a partir do Excel oficial identificado acima** quando o pipeline roda. Os testes incluídos usam dados **claramente sintéticos** apenas para garantir funcionamento das transformações, nunca para fundamentar resultados acadêmicos.

## 10. Referências principais

1. Prefeitura da Cidade do Rio de Janeiro. DATA.RIO. *Índice de Desenvolvimento Humano (IDH), por ordem decrescente, dos Municípios do Estado do Rio de Janeiro em 1991/2000/2010* (Tabela 1727), acesso 19 nov. 2026.
2. PNUD, IPEA, Fundação João Pinheiro. *Atlas do Desenvolvimento Humano no Brasil*. https://www.atlasbrasil.org.br/.
3. Wilkinson, M. D. et al. *The FAIR Guiding Principles for scientific data management and stewardship*. Scientific Data 3, 160018 (2016). https://doi.org/10.1038/sdata.2016.18.
4. Pandas. *User Guide*. https://pandas.pydata.org/docs/.
5. Plotly. *Python Graphing Library*. https://plotly.com/python/.
