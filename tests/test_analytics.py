"""Testes das consultas analíticas com funções de janela (CT-18 a CT-21)."""
import sqlite3

import pandas as pd
import pytest

from analytics.run import run, run_queries


@pytest.fixture
def con(tmp_path):
    rows = []
    # SE resolve 3 de 4 buracos em 7 dias (mediana 3); MOOCA 1 de 2; 2 semanas de dados a partir de 13/07
    for i, (sub, grupo, ab, dias, r7) in enumerate([
        ("SE", "Buraco", "2026-07-13", 1, 1), ("SE", "Buraco", "2026-07-14", 3, 1), ("SE", "Buraco", "2026-07-21", 5, 1),
        ("SE", "Buraco", "2026-07-22", 20, 0), ("MOOCA", "Buraco", "2026-07-13", 2, 1), ("MOOCA", "Buraco", "2026-07-20", None, 0),
        ("SE", "Varrição", "2026-07-02", 1, 1),          # antes de 13/07: fora da tendência
    ]):
        rows.append({"pedido_id": i, "subprefeitura": sub, "grupo": grupo, "data_abertura": ab, "dias_ate_resolver": dias,
                     "resolvido_7d": r7, "status": "Finalizada"})
    c = sqlite3.connect(tmp_path / "t.db")
    pd.DataFrame(rows).to_sql("pedidos", c, index=False)
    pd.DataFrame({"problema_id": ["a", "b", "c"], "grupo": ["Buraco"] * 3, "servico": ["s"] * 3,
                  "subprefeitura": ["SE", "SE", "MOOCA"], "distrito": ["SE", "SE", "MOOCA"], "logradouro": ["A", "B", "C"],
                  "lat": [0] * 3, "lon": [0] * 3, "pontos": [1] * 3, "pedidos_abertos": [1, 3, 2], "data_abertura": ["x"] * 3,
                  "dias_em_aberto": [5, 40, 20], "dias_de_espera": [5, 120, 40], "mediana_tipica_dias": [3] * 3,
                  "vezes_acima_do_tipico": [1.7, 13.3, 6.7]}).to_sql("lista_atrasos", c, index=False)
    yield c
    c.close()


def test_ct18_tempo_por_tipo_compara_regiao_e_cidade_com_mediana(con):
    t = run(con, "tempo_por_tipo", subprefeitura="SE").set_index(["escopo", "grupo"])
    assert t.loc[("regiao", "Buraco"), "resolvidos_7d_pct"] == 75.0
    assert t.loc[("regiao", "Buraco"), "mediana_dias"] == 4.0          # 1,3,5,20 -> (3+5)/2
    assert t.loc[("cidade", "Buraco"), "pedidos"] == 6


def test_ct19_tendencia_ignora_o_inicio_de_julho_e_calcula_lag(con):
    t = run(con, "tendencia_semanal", subprefeitura="SE", grupo=None)
    assert len(t) == 2                                                 # só as semanas a partir de 13/07
    assert t["regiao_pct"].tolist() == [100.0, 50.0]
    assert t["regiao_variacao_pp"].tolist()[1] == -50.0                # LAG
    assert t["regiao_media_3sem"].tolist()[1] == 75.0                  # média móvel


def test_ct20_ranking_com_rank_ntile_e_participacao(con):
    # o mínimo de 20 pedidos por região tira todas do ranking nesta base pequena
    assert run(con, "ranking_regioes", grupo="Buraco").empty
    con.execute("DELETE FROM pedidos")
    big = pd.DataFrame([{"pedido_id": i, "subprefeitura": s, "grupo": "Buraco", "data_abertura": "2026-08-01",
                         "dias_ate_resolver": 1, "resolvido_7d": int(i % 10 < k), "status": "Finalizada"}
                        for s, k in (("A", 9), ("B", 5), ("C", 2)) for i in range(20)])
    big.to_sql("pedidos", con, if_exists="append", index=False)
    r = run(con, "ranking_regioes", grupo="Buraco").set_index("subprefeitura")
    assert r.loc["A", "posicao"] == 1 and r.loc["C", "posicao"] == 3 and r.loc["C", "terco"] == 3
    assert r["total_regioes"].iloc[0] == 3 and r["participacao_pct"].sum() == pytest.approx(100, abs=0.5)


def test_ct21_atrasos_filtra_e_ordena(con, tmp_path):
    a = run(con, "atrasos", subprefeitura="SE", limite=10)
    assert a["logradouro"].tolist() == ["B", "A"] and a["posicao"].tolist() == [1, 2]
    assert run(con, "atrasos", limite=1)["logradouro"].tolist() == ["B"]
