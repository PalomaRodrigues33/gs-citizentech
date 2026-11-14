"""Camada silver: limpeza, tipos e colunas derivadas dos pedidos do SP156."""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg
from ingestion.sp156 import BRONZE_FILE

RENAME = {"Data de Abertura": "data_abertura", "Data de Finalização": "data_finalizacao", "Tema": "tema",
          "Assunto": "assunto", "Serviço": "servico", "Status": "status", "Latitude": "lat", "Longitude": "lon",
          "Prefeitura Operacional": "subprefeitura", "Distrito": "distrito", "Logradouro": "logradouro"}
SILVER_COLUMNS = ["pedido_id", "grupo", "servico", "status", "data_abertura", "data_finalizacao",
                  "dias_ate_resolver", "resolvido_7d", "lat", "lon", "subprefeitura", "distrito", "logradouro",
                  "local_id", "pedidos_no_local", "dia_semana"]


def clean_pedidos(bronze: pd.DataFrame, corte=None, janela=None):
    """Limpa e enriquece. Retorna (silver, relatorio_de_qualidade)."""
    corte = pd.Timestamp(corte or cfg.DATA_CORTE)
    janela = janela or cfg.JANELA_RESOLUCAO_DIAS
    df = bronze.rename(columns=RENAME)
    report = {"registros_brutos": len(df)}

    df["data_abertura"] = pd.to_datetime(df["data_abertura"], errors="coerce")
    bad = df["data_abertura"].isna()
    report["data_abertura_invalida"] = int(bad.sum())
    df = df[~bad].copy()

    df["data_finalizacao"] = pd.to_datetime(df["data_finalizacao"], errors="coerce")
    antes = df["data_finalizacao"] < df["data_abertura"]
    report["finalizacao_antes_da_abertura"] = int(antes.sum())
    df.loc[antes, "data_finalizacao"] = pd.NaT

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    b = cfg.SP_BBOX
    ok = df["lat"].between(b["lat_min"], b["lat_max"]) & df["lon"].between(b["lon_min"], b["lon_max"])
    report["sem_coordenada"] = int((df["lat"].isna() | df["lon"].isna()).sum())
    report["coordenada_fora_de_sp"] = int((~ok & df["lat"].notna() & df["lon"].notna()).sum())
    df.loc[~ok, ["lat", "lon"]] = np.nan

    df["dias_ate_resolver"] = (df["data_finalizacao"] - df["data_abertura"]).dt.days
    cancelado = df["status"].str.lower().eq("cancelada")
    janela_fechada = df["data_abertura"] <= corte - pd.Timedelta(days=janela)
    conhecido = janela_fechada & ~cancelado
    alvo = (df["dias_ate_resolver"] <= janela).astype(float)       # NaN <= 7 é falso: não finalizado = 0
    # Vazio (e não 0) quando a janela ainda não fechou ou o pedido foi cancelado: o resultado é desconhecido.
    df["resolvido_7d"] = alvo.where(conhecido)
    report["alvo_conhecido"] = int(conhecido.sum())
    report["alvo_desconhecido"] = int((~conhecido).sum())

    lat_r, lon_r = df["lat"].round(cfg.LOCAL_DECIMALS), df["lon"].round(cfg.LOCAL_DECIMALS)
    df["local_id"] = (df["grupo"] + "|" + lat_r.astype(str) + "|" + lon_r.astype(str)).where(df["lat"].notna())
    df["pedidos_no_local"] = df.groupby("local_id")["local_id"].transform("size")
    df["pedidos_no_local"] = df["pedidos_no_local"].fillna(1).astype(int)
    df["dia_semana"] = df["data_abertura"].dt.dayofweek

    df = df.sort_values(["data_abertura", "grupo"]).reset_index(drop=True)
    df["pedido_id"] = np.arange(1, len(df) + 1)
    report["registros_limpos"] = len(df)
    return df[SILVER_COLUMNS], report


def run_silver(bronze_dir: Path | None = None, silver_dir: Path | None = None, db_path: Path | None = None):
    bronze_dir = Path(bronze_dir or cfg.BRONZE_DIR)
    silver_dir = Path(silver_dir or cfg.SILVER_DIR)
    db_path = Path(db_path or cfg.DB_PATH)
    path = bronze_dir / BRONZE_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe. Rode a ingestão primeiro.")
    silver, report = clean_pedidos(pd.read_csv(path, dtype=str))
    silver_dir.mkdir(parents=True, exist_ok=True)
    silver.to_csv(silver_dir / "pedidos.csv", index=False)
    quality = pd.DataFrame([{"etapa": k, "registros": v} for k, v in report.items()])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    out = silver.copy()
    for c in ("data_abertura", "data_finalizacao"):
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    with sqlite3.connect(db_path) as con:
        out.to_sql("pedidos", con, if_exists="replace", index=False)
        quality.to_sql("qualidade_dados", con, if_exists="replace", index=False)
    return silver, quality
