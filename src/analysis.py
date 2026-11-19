"""Estatísticas reprodutíveis para as três perguntas de pesquisa."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.etl import PROCESSED, YEARS


def run(folder: Path = PROCESSED) -> dict:
    folder = Path(folder)
    wide = pd.read_csv(folder/"idhm_wide.csv")
    long = pd.read_csv(folder/"idhm_long.csv.gz")
    summary = long.groupby("ano", as_index=False).agg(
        n=("idhm", "count"), media=("idhm", "mean"), mediana=("idhm", "median"),
        desvio_padrao=("idhm", "std"), minimo=("idhm", "min"), maximo=("idhm", "max"))
    summary["amplitude"] = summary.maximo - summary.minimo
    summary["p10"] = long.groupby("ano").idhm.quantile(.1).values
    summary["p90"] = long.groupby("ano").idhm.quantile(.9).values
    summary["amplitude_p90_p10"] = summary.p90 - summary.p10
    summary.to_csv(folder/"annual_summary.csv", index=False)

    paired = wide.dropna(subset=["idhm_1991", "idhm_2010"]).copy()
    paired["ganho"] = paired.idhm_2010 - paired.idhm_1991
    paired["ganho_relativo_pct"] = 100 * paired.ganho / paired.idhm_1991
    ranking = wide.dropna(subset=["idhm_2010"]).sort_values(
        ["idhm_2010", "municipio"], ascending=[False, True]).copy()
    ranking["posicao_2010"] = ranking.idhm_2010.rank(method="min", ascending=False).astype(int)
    ranking.to_csv(folder/"ranking_2010.csv", index=False)
    gains = paired.sort_values("ganho", ascending=False)
    gains.to_csv(folder/"variacao_municipios.csv", index=False)

    def finite_or_null(x):
        return float(x) if x is not None and pd.notna(x) and np.isfinite(x) else None
    def rec(s):
        return [{k:(int(v) if isinstance(v, (np.integer,)) else finite_or_null(v))
                 for k,v in row.items()} for row in s.to_dict("records")]
    def short(s):
        return [{"municipio": str(r.municipio), "idhm_2010": finite_or_null(r.idhm_2010)}
                for r in s.itertuples()]
    metrics = {
        "title": "IDHM municipal do Estado do Rio de Janeiro: 1991, 2000, 2010",
        "years": list(YEARS), "municipalities": len(wide),
        "paired_municipalities": len(paired),
        "annual_summary": rec(summary[["ano", "n", "media", "mediana", "desvio_padrao", "minimo", "maximo", "amplitude", "p10", "p90", "amplitude_p90_p10"]]),
        "mean_paired_gain": finite_or_null(paired.ganho.mean()),
        "median_paired_gain": finite_or_null(paired.ganho.median()),
        "mean_paired_percent_gain": finite_or_null(paired.ganho_relativo_pct.mean()),
        "all_positive_gains": bool((paired.ganho > 0).all()),
        "positive_gain_count": int((paired.ganho > 0).sum()),
        "negative_gain_count": int((paired.ganho < 0).sum()),
        "unchanged_count": int((paired.ganho == 0).sum()),
        "corr_spearman_baseline_gain": finite_or_null(paired.idhm_1991.corr(paired.ganho, method="spearman")),
        "corr_pearson_baseline_gain": finite_or_null(paired.idhm_1991.corr(paired.ganho, method="pearson")),
        "top5_2010": short(ranking.head(5)),
        "bottom5_2010": short(ranking.tail(5).iloc[::-1]),
        "largest_absolute_gains": [{"municipio": str(r.municipio), "ganho": finite_or_null(r.ganho)} for r in gains.head(5).itertuples()],
        "smallest_absolute_gains": [{"municipio": str(r.municipio), "ganho": finite_or_null(r.ganho)} for r in gains.tail(5).iloc[::-1].itertuples()],
        "rj_capital_2010": finite_or_null(wide.loc[wide.municipio.str.casefold() == "rio de janeiro", "idhm_2010"].iloc[0]) if (wide.municipio.str.casefold() == "rio de janeiro").any() else None,
    }
    (folder/"metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Análise: {len(wide)} municípios, {len(paired)} pares 1991–2010")
    return metrics


if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder", type=Path, default=PROCESSED)
    run(p.parse_args().folder)
