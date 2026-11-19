"""Baixa o Excel ORIGINAL do Data.Rio com arquivo bruto e metadados auditáveis."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ITEM_ID = "5f39ef2738b7488bba7142b666a70f0b"
DATA_URL = f"https://www.arcgis.com/sharing/rest/content/items/{ITEM_ID}/data"
SOURCE_PAGE = f"https://www.data.rio/documents/{ITEM_ID}/about"
RAW = ROOT / "data/raw/idhm_municipios_rj_1991_2000_2010.xls"
METADATA = ROOT / "data/raw/source_provenance.json"


def fetch(destination: Path = RAW, force: bool = False, retries: int = 3) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and not force:
        verify_excel(destination.read_bytes())
        return destination
    last_error = None
    for attempt in range(retries):
        try:
            request = Request(DATA_URL, headers={
                "User-Agent": "IDHM-RJ-academic-research/1.0 (+https://www.data.rio/)",
                "Accept": "application/vnd.ms-excel,application/octet-stream,*/*",
            })
            with urlopen(request, timeout=90) as response:
                raw = response.read()
            verify_excel(raw)
            tmp = destination.with_suffix(destination.suffix + ".part")
            tmp.write_bytes(raw)
            os.replace(tmp, destination)
            info = {
                "dataset_page": SOURCE_PAGE, "download_url": DATA_URL,
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "file_bytes": len(raw),
                "source_title": "Índice de Desenvolvimento Humano (IDH), por ordem decrescente, dos Municípios do Estado do Rio de Janeiro em 1991/2000/2010",
                "source_publisher": "Prefeitura da Cidade do Rio de Janeiro / DATA.RIO",
                "source_license": "CC BY 4.0 (conforme metadados do item no ArcGIS)",
            }
            METADATA.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Download confirmado: {destination} ({len(raw)} bytes, SHA256 {info['sha256']})")
            return destination
        except (OSError, HTTPError, URLError, ValueError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)
    raise RuntimeError(f"Não foi possível obter o Excel oficial em {DATA_URL}: {last_error}. "
                       f"Baixe manualmente na página {SOURCE_PAGE} e salve como {destination}")


def verify_excel(raw: bytes) -> None:
    if raw.startswith(bytes.fromhex("D0CF11E0A1B11AE1")) or raw.startswith(b"PK\\x03\\x04"):
        return
    if raw.startswith(b"PK\x03\x04"):
        return
    if raw[:40].lstrip().lower().startswith((b"<html", b"<!doctype")):
        raise ValueError("O download retornou HTML (possível bloqueio), não um Excel")
    raise ValueError(f"Assinatura não identificada como Excel: {raw[:16].hex()}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="Rebaixa mesmo se já houver arquivo")
    p.add_argument("--output", type=Path, default=RAW)
    a = p.parse_args()
    fetch(a.output, a.force)
