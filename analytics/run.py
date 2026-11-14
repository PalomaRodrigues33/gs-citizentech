"""Consultas analíticas em SQL com funções de janela, uma por pergunta do app."""
import sqlite3
from pathlib import Path

import pandas as pd

import config as cfg

SQL_DIR = Path(__file__).resolve().parent / "sql"
QUERIES = ("tempo_por_tipo", "tendencia_semanal", "ranking_regioes", "atrasos")


def sql(name: str) -> str:
    if name not in QUERIES:
        raise ValueError(f"consulta desconhecida: {name}")
    return (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")


def run(con: sqlite3.Connection, name: str, subprefeitura=None, grupo=None, limite=50) -> pd.DataFrame:
    """Executa uma consulta com parâmetros nomeados (sempre parametrizada, nunca texto concatenado)."""
    params = {"subprefeitura": subprefeitura, "grupo": grupo, "limite": int(limite), "inicio": cfg.TENDENCIA_INICIO}
    return pd.read_sql(sql(name), con, params=params)


def run_queries(db_path: Path | None = None, gold_dir: Path | None = None) -> dict:
    db_path = Path(db_path or cfg.DB_PATH)
    gold_dir = Path(gold_dir or cfg.GOLD_DIR)
    gold_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    with sqlite3.connect(db_path) as con:
        for name in QUERIES:
            df = run(con, name, limite=500)
            df.to_csv(gold_dir / f"an_{name}.csv", index=False)
            df.to_sql(f"an_{name}", con, if_exists="replace", index=False)
            out[name] = df
    return out
