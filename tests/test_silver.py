"""Testes da camada silver (CT-06 a CT-12)."""
import sqlite3

import pandas as pd
import pytest

import config as cfg
from pipeline.silver import clean_pedidos, run_silver

COLS = ["Data de Abertura", "Data de Finalização", "Tema", "Assunto", "Serviço", "Status", "Logradouro",
        "Latitude", "Longitude", "Prefeitura Operacional", "Distrito", "grupo"]


def _b(**kw):
    base = {"Data de Abertura": "2026-07-01", "Data de Finalização": "2026-07-04", "Tema": "t", "Assunto": "a",
            "Serviço": "Tapa-buraco", "Status": "Finalizada", "Logradouro": "Rua A", "Latitude": "-23.55",
            "Longitude": "-46.63", "Prefeitura Operacional": "SE", "Distrito": "SE", "grupo": "Buraco"}
    base.update(kw)
    return base


def _clean(rows):
    return clean_pedidos(pd.DataFrame(rows, columns=COLS), corte="2026-09-30", janela=7)


def test_ct06_data_invalida_remove_a_linha():
    s, r = _clean([_b(), _b(**{"Data de Abertura": "nao-e-data"})])
    assert len(s) == 1 and r["data_abertura_invalida"] == 1


def test_ct07_finalizacao_antes_da_abertura_e_anulada():
    s, r = _clean([_b(**{"Data de Finalização": "2026-06-20"})])
    assert r["finalizacao_antes_da_abertura"] == 1 and pd.isna(s.iloc[0]["dias_ate_resolver"])


def test_ct08_coordenada_invalida_ou_fora_de_sp_e_anulada_sem_perder_a_linha():
    s, r = _clean([_b(Latitude="0", Longitude="0"), _b(Latitude="", Longitude="")])
    assert len(s) == 2 and s["lat"].isna().all()
    assert r["coordenada_fora_de_sp"] == 1 and r["sem_coordenada"] == 1


def test_ct09_alvo_7_dias_nos_tres_casos():
    s, _ = _clean([
        _b(**{"Data de Finalização": "2026-07-04"}),                                 # 3 dias -> 1
        _b(**{"Data de Finalização": "2026-07-20"}),                                 # 19 dias -> 0
        _b(**{"Data de Finalização": "", "Status": "Aberto"}),                       # aberto, janela fechada -> 0
    ])
    assert s["resolvido_7d"].tolist() == [1.0, 0.0, 0.0]


def test_ct10_alvo_desconhecido_para_recentes_e_cancelados():
    s, r = _clean([
        _b(**{"Data de Abertura": "2026-09-28", "Data de Finalização": "", "Status": "Aberto"}),   # janela aberta
        _b(Status="Cancelada"),
    ])
    assert s["resolvido_7d"].isna().all() and r["alvo_desconhecido"] == 2


def test_ct11_pedidos_no_mesmo_local_viram_sinal_de_apoio():
    s, _ = _clean([_b(), _b(), _b(Latitude="-23.60", Longitude="-46.70"), _b(grupo="Bueiro")])
    por = s.groupby(["grupo", "lat"])["pedidos_no_local"].max()
    assert por[("Buraco", -23.55)] == 2 and por[("Buraco", -23.60)] == 1 and por[("Bueiro", -23.55)] == 1


def test_ct12_run_silver_grava_csv_e_banco(tmp_path):
    (tmp_path / "bronze").mkdir()
    pd.DataFrame([_b(), _b()], columns=COLS).to_csv(tmp_path / "bronze" / "sp156_recorte.csv", index=False)
    s, q = run_silver(tmp_path / "bronze", tmp_path / "silver", tmp_path / "t.db")
    with sqlite3.connect(tmp_path / "t.db") as con:
        n = con.execute("select count(*) from pedidos").fetchone()[0]
        m = con.execute("select count(*) from qualidade_dados").fetchone()[0]
    assert n == len(s) == 2 and m == len(q)
