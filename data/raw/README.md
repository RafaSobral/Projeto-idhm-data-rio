# Planilha de origem

Base oficial: **Índice de Desenvolvimento Humano (IDH), por ordem decrescente, dos Municípios do Estado do Rio de Janeiro em 1991/2000/2010** (Tabela 1727).

Página do catálogo: https://www.data.rio/documents/5f39ef2738b7488bba7142b666a70f0b/about

Download direto via ArcGIS: https://www.arcgis.com/sharing/rest/content/items/5f39ef2738b7488bba7142b666a70f0b/data

Execute `python scripts/fetch_data.py`, que salva o arquivo original como `data/raw/idhm_municipios_rj_1991_2000_2010.xls` e registra SHA-256 em `source_provenance.json`. Alternativamente, baixe manualmente pela página pública e salve com esse nome. O pipeline **não modifica o arquivo bruto**. O workflow de publicação coleta e armazena uma cópia do bruto no repositório.
