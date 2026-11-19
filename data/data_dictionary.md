# Dicionário de dados: Tabela 1727, municípios do RJ, IDHM 1991/2000/2010

**Fonte primária:** Prefeitura da Cidade do Rio de Janeiro / [DATA.RIO](https://www.data.rio/documents/5f39ef2738b7488bba7142b666a70f0b/about) (Tabela 1727).

**Grão bruto:** linha municipal da planilha publicada, com um valor de IDHM para cada ano censitário (1991, 2000 e 2010), conforme disponibilidade.
**Grão processado (`idhm_long.csv.gz`):** um registro por município e ano (pode conter `idhm` nulo).
**Tipos:** `string` (texto), `int64` (inteiro), `float64` (número decimal), `boolean` (indicador lógico).

## `data/processed/idhm_wide.csv`

| Variável | Tipo | Descrição | Valores / formato |
|---|---|---|---|
| `municipio` | string | Nome de município tal como apresentado no arquivo de origem, com normalização de espaços | UTF-8 |
| `idhm_1991` | float64 (nullable) | Índice de Desenvolvimento Humano Municipal em 1991 | 0 a 1, ponto decimal; nulos preservados |
| `idhm_2000` | float64 (nullable) | Índice em 2000 | 0 a 1; nulos preservados |
| `idhm_2010` | float64 (nullable) | Índice em 2010 | 0 a 1; nulos preservados |
| `linha_origem` | int64 | Linha na aba interpretada do Excel, usada na rastreabilidade aproximada | inteiro positivo; a contagem considera linhas não vazias após limpeza inicial |
| `variacao_1991_2010` | float64 (nullable) | Diferença absoluta IDHM 2010 − IDHM 1991 | pontos no índice; nulo se um extremo ausente |
| `faixa_2010` | string | Faixa de IDHM 2010: muito baixo, baixo, médio, alto, muito alto | Classes de 0–0,499; 0,500–0,599; 0,600–0,699; 0,700–0,799; 0,800–1; 'Sem dado' para ausentes |

## `data/processed/idhm_long.csv.gz`

| Variável | Tipo | Descrição | Valores / formato |
|---|---|---|---|
| `municipio` | string | Nome do município | UTF-8 |
| `ano` | int64 | Ano de observação censitária | 1991, 2000, 2010 |
| `idhm` | float64 (nullable) | Índice de Desenvolvimento Humano Municipal | [0,1], com nulos preservados |
| `faixa_idhm` | string | Categoria de desenvolvimento | Faixas definidas acima |
| `registro_ausente` | boolean | Marca se o IDHM está ausente na observação | true/false |

## Tabelas de resultados

- `annual_summary.csv`: colunas `ano`, `n`, `media`, `mediana`, `desvio_padrao`, `minimo`, `maximo`, `amplitude`, `p10`, `p90`, `amplitude_p90_p10`; cada linha representa um ano, agregando municípios com IDHM disponível.
- `ranking_2010.csv`: colunas da tabela ampla e `posicao_2010`; empate recebe a mesma posição (`rank(method='min')`).
- `variacao_municipios.csv`: apenas municípios com valores válidos em 1991 e 2010, inclui `ganho` e `ganho_relativo_pct`.
- `quality_report.json`: identificação das colunas, aba usada, número de observações e faltantes.
- `metrics.json`: estatísticas e observações usadas na redação e nos gráficos.
- `data/raw/source_provenance.json`: URL, SHA-256, tamanho e data UTC do download original.

A média é **simples por município**, nunca ponderada pelo tamanho de população. A diferença de IDHM é medida em **pontos do índice**, não em anos de vida ou percentuais. Valores faltantes não são preenchidos. Os scripts falham caso não consigam distinguir registros municipais do layout editorial da planilha original.
