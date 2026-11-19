"""Fixtures sintéticas testam o parser, NÃO representam resultados do DATA.RIO."""
import math
from pathlib import Path
import numpy as np
import pandas as pd
from src.etl import parse_sheet, number, classify, parse_excel


def fixture(headers=True, missing=False):
    rows = [
        ["Tabela 1727 — Índice de Desenvolvimento Humano Municipal",None,None,None,None,None],
        ["Ordem", "Município", "IDHM 1991", "IDHM 2000", "IDHM 2010", "Observações"],
    ]
    for i in range(1,93):
        a=round(.31+i*.001,3)
        b=round(.45+i*.001,3)
        c=round(.57+i*.001,3)
        rows.append([i, f"Município de Exemplo {i:03}",str(a).replace('.',','),str(b).replace('.',','),str(c).replace('.',','),None])
    if missing:
        rows[-1][2]=None
    rows.append([None,"Fonte: DATA.RIO",None,None,None,None])
    return pd.DataFrame(rows)


def test_parse_92_municipios():
    df,report=parse_sheet(fixture())
    assert len(df)==92
    assert report['year_columns_indices']=={'1991':2,'2000':3,'2010':4}
    assert df.idhm_2010.iloc[0] == .571
    assert int(df.idhm_1991.isna().sum()) == 0


def test_nulos_nao_imputados():
    df,report=parse_sheet(fixture(missing=True))
    assert len(df)==92
    assert math.isnan(df.idhm_1991.iloc[-1])
    assert report['missing_values']['1991']==1


def test_rejeita_layout_inesperado():
    import pytest
    with pytest.raises(ValueError):parse_sheet(pd.DataFrame({'a':['abc','def'],'b':['xx','yy']}))


def test_classificacao_e_decimal():
    assert number('0,799') == .799
    assert number(' - ') != number(' - ')
    assert classify(.799)=='Alto'
    assert classify(.8)=='Muito alto'
    assert classify(np.nan)=='Sem dado'


def test_leitura_csv_simulado(tmp_path: Path):
    source=tmp_path/'fixture.csv'
    fixture().to_csv(source,index=False,header=False)
    df,_=parse_excel(source)
    assert len(df)==92


def test_cabecalhos_em_ordem_invertida():
    original=fixture()
    rev=original.iloc[:,[0,1,4,3,2,5]].copy()
    df,report=parse_sheet(rev)
    assert report['year_columns_indices']=={'1991':4,'2000':3,'2010':2}
    assert df.idhm_1991.iloc[0]==.311
    assert df.idhm_2010.iloc[0]==.571


def test_rankings_independentes_junta_por_municipio():
    # Ordem municipal diferente por ano: merge por linha geraria resultado falso.
    import random
    rng=random.Random(13)
    mun=[f"Município Teste {i:03}" for i in range(1,93)]
    shuffled=mun.copy();rng.shuffle(shuffled)
    reverse=list(reversed(mun))
    rows=[["pos 1991","Município","1991","pos 2000","Município","2000","pos 2010","Município","2010"]]
    for i,(a,b,c) in enumerate(zip(mun,shuffled,reverse),start=1):
        v=lambda n,y: round((.3 if y==1991 else .45 if y==2000 else .6) + int(n[-3:])*.001,3)
        rows.append([i,a,v(a,1991),i,b,v(b,2000),i,c,v(c,2010)])
    df,report=parse_sheet(pd.DataFrame(rows))
    row=df[df.municipio=='Município Teste 001'].iloc[0]
    assert len(df)==92
    assert row.idhm_1991==.301 and row.idhm_2000==.451 and row.idhm_2010==.601
    assert report['layout_detectado']=='rankings_independentes'
