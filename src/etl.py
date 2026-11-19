"""Extração e harmonização rastreável da planilha original da tabela 1727 (DATA.RIO).

A origem é uma publicação tabular em Excel, não um CSV com cabeçalho estável.
O parser considera variações de colunas e linhas de título, sem inventar valores ausentes.
Ao detectar uma estrutura inesperada, falha com mensagem diagnóstica em vez de adivinhar.
"""
from __future__ import annotations
import argparse
import itertools
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/idhm_municipios_rj_1991_2000_2010.xls"
PROCESSED = ROOT / "data/processed"
YEARS = (1991, 2000, 2010)


def text_norm(value: Any) -> str:
    """Remove duplicação de espaços e normaliza para comparação, não para exibição."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def folding(value: str) -> str:
    value = unicodedata.normalize("NFKD", text_norm(value)).encode("ascii", "ignore").decode()
    return value.lower()


def number(value: Any) -> float:
    if pd.isna(value) or isinstance(value, bool):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    raw = re.sub(r"[\s\u00a0\*]+", "", str(value)).strip()
    if raw in ("", "—", "-", "..", "...", "s/d", "nd", "n/d"):
        return np.nan
    if re.fullmatch(r"\d+[.,]\d+", raw):
        return float(raw.replace(",", "."))
    return np.nan


def is_idhm(value: Any) -> bool:
    n = number(value)
    return bool(np.isfinite(n) and 0.15 <= n <= 1)


def municipality_label(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    s = folding(value)
    if len(s) < 3 or len(s) > 75 or not re.search(r"[a-z]{3}", s):
        return False
    if re.search(r"(fonte|tabela|indice|idh|classificacao|municipios|posicao|ranking|ordem decrescente|\bano\b|\bnotas?\b|\btotal\b|\bmedia\b|\brio de janeiro\s*\(estado\))", s):
        return False
    if re.fullmatch(r"\d+", s) or "http" in s or "@" in s:
        return False
    return True


def infer_candidates(grid: pd.DataFrame, header_limit: int = 35) -> list[dict]:
    """Pontua combinações (município, 1991, 2000, 2010) por cobertura das linhas."""
    grid = grid.dropna(axis=1, how="all").dropna(axis=0, how="all")
    grid.columns = range(grid.shape[1])
    rows = grid.values.tolist()
    columns = list(range(grid.shape[1]))
    if len(columns) > 80:
        raise ValueError("Planilha com colunas demais: revisão de estrutura necessária")
    # Identificar rótulos de ano nas primeiras linhas (valor exato ou título textual).
    hints = {year: set() for year in YEARS}
    for row in rows[:header_limit]:
        for j, cell in enumerate(row):
            s = text_norm(cell)
            for year in YEARS:
                if re.search(rf"(?<!\d){year}(?!\d)", s):
                    hints[year].add(j)
    value_cols = []
    for j in columns:
        count = sum(is_idhm(row[j]) for row in rows)
        if count >= 10:
            value_cols.append(j)
    candidates = []
    for combination in itertools.combinations(value_cols, 3):
        if max(combination) - min(combination) > 18:
            continue
        complete = [i for i, row in enumerate(rows) if all(is_idhm(row[j]) for j in combination)]
        if len(complete) < 12:
            continue
        for yc in itertools.permutations(combination):
            # yc armazena na ordem lógica (1991, 2000, 2010), não na ordem física.
            evidence = sum((yc[k] in hints[year]) for k, year in enumerate(YEARS))
            # Quando o cabeçalho explicita os três anos, nunca adivinhar outra ordem.
            year_header_coverage = sum(any(hints[y] & set(combination)) for y in YEARS)
            if year_header_coverage >= 2 and evidence < 2:
                continue
            for name_col in columns:
                if name_col in combination or name_col > max(combination):
                    continue
                names = [(i, text_norm(rows[i][name_col])) for i in complete if municipality_label(rows[i][name_col])]
                if not names:
                    continue
                unique = len({folding(n) for _, n in names})
                left_bonus = 4 if name_col < min(combination) else 0
                name_hint = 0
                for row in rows[:header_limit]:
                    if re.search(r"munic[ií]p", folding(row[name_col])):
                        name_hint = 5
                        break
                order_bonus = 2 if list(yc)==sorted(yc) else 0
                score = len(names)*3 + unique + 25*evidence + left_bonus + name_hint + order_bonus - (max(combination)-min(combination))*0.2
                candidates.append({"name_col": name_col, "year_cols": yc, "complete": len(names),
                                   "score": score, "rows": len(rows), "grid": grid,
                                   "evidence": evidence})
    return sorted(candidates, key=lambda x:x["score"], reverse=True)


def parse_sheet(grid: pd.DataFrame, sheet_name: str = "Sheet1") -> tuple[pd.DataFrame, dict]:
    options = infer_candidates(grid)
    if not options:
        # Guardar a primeira amostra de células ajuda a corrigir planilhas publicadas em layout exótico.
        preview = grid.head(12).fillna("").astype(str).to_string(index=False, header=False, max_cols=12)
        raise ValueError(f"Não foi possível identificar colunas de IDHM; prévia:\n{preview}")
    opt = options[0]
    grid = opt["grid"]
    name_col, year_cols = opt["name_col"], opt["year_cols"]
    # Algumas tabelas publicadas exibem três rankings independentes, cada qual
    # com sua coluna de município. Fazer merge por posição seria um erro grave.
    def preferred_name_col(year_col):
        matches=[]
        for j in range(year_col):
            valid_rows=[r for r in grid.itertuples(index=False,name=None) if is_idhm(r[year_col])]
            if not valid_rows: continue
            names=[text_norm(r[j]) for r in valid_rows if municipality_label(r[j])]
            if len(names)<max(35,int(len(valid_rows)*.65)):continue
            unique=len({folding(x) for x in names})
            header_hits=0
            for row in grid.head(35).itertuples(index=False,name=None):
                if re.search(r"\bmunicip",folding(row[j])):
                    header_hits=1
                    break
            matches.append((len(names)+unique+header_hits*140-.12*(year_col-j),j))
        return max(matches)[1] if matches else name_col

    year_names=[preferred_name_col(j) for j in year_cols]
    independent_layout=len(set(year_names))>1
    records=[]
    if independent_layout:
        # Cada coluna de ano é associada ao seu próprio município e as
        # classificações são consolidadas por chave nominal, nunca por posição.
        by_key={}
        for y, col, name_col_y in zip(YEARS, year_cols, year_names):
            seen=set()
            for excel_row, row in enumerate(grid.itertuples(index=False,name=None),start=1):
                name=text_norm(row[name_col_y])
                value=number(row[col])
                if not municipality_label(name) or not is_idhm(value):continue
                if re.search(r"\b(estado do rio de janeiro|total|media estadual)\b",folding(name)): continue
                key=folding(name)
                if key in seen:
                    raise ValueError(f"Nome duplicado no ranking de {y}: {name}")
                seen.add(key)
                by_key.setdefault(key,{"municipio":name,"idhm_1991":np.nan,"idhm_2000":np.nan,"idhm_2010":np.nan,"linha_origem":excel_row})[f"idhm_{y}"]=value
        records=list(by_key.values())
    else:
        for excel_row, row in enumerate(grid.itertuples(index=False, name=None), start=1):
            name = text_norm(row[name_col]); nums = [number(row[j]) for j in year_cols]
            valid = [float(n) if np.isfinite(n) and 0.15 <= n <= 1 else np.nan for n in nums]
            if not municipality_label(name) or sum(np.isfinite(v) for v in valid) < 2:
                continue
            if re.search(r"\b(estado do rio de janeiro|total|media estadual)\b", folding(name)):
                continue
            records.append({"municipio": name, "idhm_1991": valid[0], "idhm_2000": valid[1],
                            "idhm_2010": valid[2], "linha_origem": excel_row})
    df = pd.DataFrame.from_records(records)
    if df.empty:
        raise ValueError("Encontrou cabeçalho, mas nenhuma observação municipal válida")
    key = df["municipio"].map(folding)
    duplicated = df[key.duplicated(keep=False)]
    if not duplicated.empty:
        raise ValueError(f"Municípios duplicados: {duplicated['municipio'].tolist()[:12]}; revisar a estrutura")
    if not 60 <= len(df) <= 100:
        raise ValueError(f"Foram extraídos apenas {len(df)} registros: esperado ~92 municípios fluminenses. "
                         f"Colunas detectadas: município={name_col}, anos={year_cols}")
    report = {"sheet": sheet_name, "rows_extracted": len(df), "name_column_index": name_col,
              "year_columns_indices": dict(zip(map(str, YEARS), year_cols)),
              "candidate_score": round(opt["score"],2), "complete_rows": opt["complete"],
              "year_header_matches": opt["evidence"],
              "layout_detectado": "rankings_independentes" if independent_layout else "linhas_municipais_unicas",
              "colunas_nome_por_ano": dict(zip(map(str,YEARS),year_names)),
              "missing_values": {str(y): int(df[f"idhm_{y}"].isna().sum()) for y in YEARS},
              "duplicate_municipalities": 0}
    return df, report


def parse_excel(source: Path) -> tuple[pd.DataFrame, dict]:
    source = Path(source)
    if source.suffix.lower() == ".csv":
        grid = pd.read_csv(source, header=None, dtype=object)
        return parse_sheet(grid, source.name)
    # xlrd para .xls (formato binário Excel); openpyxl para xlsx.
    signature = source.read_bytes()[:8]
    engine = "openpyxl" if signature.startswith(b"PK\x03\x04") else "xlrd"
    sheets = pd.read_excel(source, sheet_name=None, header=None, dtype=object, engine=engine)
    candidates = []
    errors = {}
    for name, grid in sheets.items():
        try:
            parsed, report = parse_sheet(grid, name)
            candidates.append((parsed, report))
        except ValueError as exc:
            errors[name] = str(exc)
    if not candidates:
        raise ValueError("Nenhuma aba foi identificada. Diagnóstico: " + json.dumps(errors, ensure_ascii=False))
    candidates.sort(key=lambda p: (len(p[0]), -sum(p[1]["missing_values"].values())), reverse=True)
    return candidates[0]


def classify(v: float) -> str:
    if pd.isna(v): return "Sem dado"
    if v < .5: return "Muito baixo"
    if v < .6: return "Baixo"
    if v < .7: return "Médio"
    if v < .8: return "Alto"
    return "Muito alto"


def run(source: Path = RAW, output: Path = PROCESSED) -> dict:
    wide, report = parse_excel(Path(source))
    output.mkdir(exist_ok=True, parents=True)
    wide = wide.sort_values("municipio").reset_index(drop=True)
    wide["variacao_1991_2010"] = wide.idhm_2010 - wide.idhm_1991
    wide["faixa_2010"] = wide.idhm_2010.map(classify)
    long = wide.melt(id_vars=["municipio"], value_vars=[f"idhm_{x}" for x in YEARS],
                     var_name="ano", value_name="idhm")
    long["ano"] = long.ano.str.replace("idhm_", "", regex=False).astype(int)
    long["faixa_idhm"] = long.idhm.map(classify)
    long["registro_ausente"] = long.idhm.isna()
    long.to_csv(output/"idhm_long.csv.gz", index=False, compression="gzip")
    wide.to_csv(output/"idhm_wide.csv", index=False, encoding="utf-8")
    report["observacoes_municipio_ano"] = int(len(long))
    report["observacoes_validas"] = int(long.idhm.notna().sum())
    report["observacoes_ausentes"] = int(long.idhm.isna().sum())
    report["analysis_coverage"] = "Valores ausentes permanecem nulos; nenhuma imputação"
    (output/"quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=RAW)
    parser.add_argument("--output", type=Path, default=PROCESSED)
    args = parser.parse_args()
    run(args.source, args.output)
