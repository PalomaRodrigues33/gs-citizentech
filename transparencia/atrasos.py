"""Lista pública de atrasos: rua + tipo de serviço com pedidos ainda abertos.

Ordenada por dias_de_espera = soma dos dias em aberto de todos os pedidos daquele problema.
"""
import numpy as np
import pandas as pd

import config as cfg

COLUMNS = ["problema_id", "grupo", "servico", "subprefeitura", "distrito", "logradouro", "lat", "lon",
           "pontos", "pedidos_abertos", "data_abertura", "dias_em_aberto", "dias_de_espera", "mediana_tipica_dias",
           "vezes_acima_do_tipico", "posicao"]


def typical_days(silver: pd.DataFrame) -> pd.DataFrame:
    """Mediana de dias até resolver por subprefeitura e grupo (só pedidos finalizados)."""
    fin = silver.dropna(subset=["dias_ate_resolver"])
    return (fin.groupby(["subprefeitura", "grupo"])["dias_ate_resolver"].median()
            .rename("mediana_tipica_dias").reset_index())


def open_problems(silver: pd.DataFrame) -> pd.DataFrame:
    """Agrupa os pedidos ainda abertos por problema (rua + tipo, ou ponto quando não há rua)."""
    occ = silver[silver["status"].isin(["Aberto", "Em Andamento"]) & silver["local_id"].notna()].copy()
    rua = occ["logradouro"].fillna("").str.strip().str.upper()
    occ["problema_id"] = (occ["subprefeitura"].fillna("") + "|" + occ["grupo"] + "|" + rua).where(rua != "", occ["local_id"])
    g = occ.sort_values("data_abertura").groupby("problema_id")
    prob = g.agg(grupo=("grupo", "first"), servico=("servico", lambda x: x.mode().iat[0]),
                 subprefeitura=("subprefeitura", "first"), distrito=("distrito", "first"),
                 logradouro=("logradouro", "first"), lat=("lat", "first"), lon=("lon", "first"),
                 pontos=("local_id", "nunique"), pedidos_abertos=("pedido_id", "size"),
                 data_abertura=("data_abertura", "min")).reset_index()
    prob["dias_em_aberto"] = (pd.Timestamp(cfg.DATA_CORTE) - prob["data_abertura"]).dt.days.clip(lower=0)
    # dias de espera somados de todos os pedidos (não só o mais antigo)
    occ["espera"] = (pd.Timestamp(cfg.DATA_CORTE) - occ["data_abertura"]).dt.days.clip(lower=0)
    prob = prob.merge(occ.groupby("problema_id")["espera"].sum().rename("dias_de_espera").reset_index(), on="problema_id")
    return prob


def build_list(silver: pd.DataFrame) -> pd.DataFrame:
    prob = open_problems(silver).merge(typical_days(silver), on=["subprefeitura", "grupo"], how="left")
    tip = prob["mediana_tipica_dias"].clip(lower=1)       # mediana 0 (mesmo dia) conta como 1 dia
    prob["vezes_acima_do_tipico"] = (prob["dias_em_aberto"] / tip).round(1)
    prob = prob.sort_values(["dias_de_espera", "dias_em_aberto"], ascending=False).reset_index(drop=True)
    prob["posicao"] = np.arange(1, len(prob) + 1)
    return prob[COLUMNS]
