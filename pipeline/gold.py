"""Camada gold: lista pública de atrasos (CSV e tabela no banco)."""
import sqlite3
from pathlib import Path

import pandas as pd

import config as cfg


def write_gold(atrasos: pd.DataFrame, gold_dir: Path | None = None, db_path: Path | None = None):
    gold_dir = Path(gold_dir or cfg.GOLD_DIR)
    db_path = Path(db_path or cfg.DB_PATH)
    gold_dir.mkdir(parents=True, exist_ok=True)
    a = atrasos.copy()
    a["data_abertura"] = pd.to_datetime(a["data_abertura"]).dt.strftime("%Y-%m-%d")
    a.to_csv(gold_dir / "lista_atrasos.csv", index=False)
    with sqlite3.connect(db_path) as con:
        a.to_sql("lista_atrasos", con, if_exists="replace", index=False)
        for old in ("fila_priorizada", "equipamentos", "cidadaos", "ocorrencias_app", "apoios_app",
                    "an_ranking_subprefeituras", "an_serie_diaria", "an_variacao_semanal",
                    "an_mediana_por_grupo", "an_faixas_prioridade"):
            con.execute(f"DROP TABLE IF EXISTS {old}")   # restos da versão anterior
