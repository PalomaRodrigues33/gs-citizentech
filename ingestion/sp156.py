"""Ingestão: lê o arquivo original do SP156 e grava o recorte de zeladoria na bronze.

Bronze = as colunas do original + `grupo`. Nada é corrigido aqui; limpeza e tipos ficam na silver.
"""
import json
from pathlib import Path

import pandas as pd

import config as cfg

BRONZE_FILE = "sp156_recorte.csv"
REPORT_FILE = "ingestao_relatorio.json"
REQUIRED = ["Data de Abertura", "Data de Finalização", "Tema", "Assunto", "Serviço", "Status",
            "Latitude", "Longitude", "Prefeitura Operacional", "Distrito"]


def find_source(raw_dir: Path | None = None) -> Path:
    """Arquivo indicado em SP156_FILE ou o primeiro .xlsx/.csv de data/raw."""
    if cfg.SP156_FILE:
        p = Path(cfg.SP156_FILE)
        if not p.exists():
            raise FileNotFoundError(f"SP156_FILE aponta para um arquivo que não existe: {p}")
        return p
    raw_dir = Path(raw_dir or cfg.RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)      # não vem no repositório
    files = sorted(list(raw_dir.glob("*.xlsx")) + list(raw_dir.glob("*.csv")))
    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo do SP156 encontrado.\n"
            f"Baixe 'Solicitações' do 3º trimestre de 2026 em\n"
            f"  https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156\n"
            f"e salve o .xlsx (ou .csv) nesta pasta, que acabou de ser criada:\n"
            f"  {raw_dir.resolve()}")
    return files[0]


def read_raw(path: Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str, sep=None, engine="python")
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no arquivo do SP156: {missing}")
    return df


def classify(servico) -> str | None:
    if not isinstance(servico, str):
        return None
    s = servico.strip().lower()
    for grupo, prefixos in cfg.GRUPOS.items():
        if s.startswith(prefixos):
            return grupo
    return None


def run_ingestion(source: Path | None = None, bronze_dir: Path | None = None):
    """Lê o raw, recorta os grupos e grava a bronze. Retorna (recorte, relatorio)."""
    source = Path(source) if source else find_source()
    bronze_dir = Path(bronze_dir or cfg.BRONZE_DIR)
    raw = read_raw(source)
    grupo = raw["Serviço"].map(classify)
    recorte = raw.assign(grupo=grupo)[grupo.notna()].reset_index(drop=True)
    report = {
        "arquivo_origem": source.name,
        "linhas_lidas": int(len(raw)),
        "linhas_no_recorte": int(len(recorte)),
        "linhas_fora_do_escopo": int(len(raw) - len(recorte)),
        "por_grupo": {k: int(v) for k, v in recorte["grupo"].value_counts().items()},
    }
    bronze_dir.mkdir(parents=True, exist_ok=True)
    recorte.to_csv(bronze_dir / BRONZE_FILE, index=False)
    (bronze_dir / REPORT_FILE).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return recorte, report


if __name__ == "__main__":
    _, rep = run_ingestion()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
