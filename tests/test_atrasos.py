"""Testes da lista pública de atrasos (CT-15 a CT-17)."""
import pandas as pd
import pytest

from transparencia.atrasos import build_list, open_problems


def _p(pid, grupo="Buraco", rua="Rua A", sub="SE", lat=-23.5, abertura="2026-09-01", status="Aberto", dias=None):
    return {"pedido_id": pid, "grupo": grupo, "servico": "Tapa-buraco", "status": status, "subprefeitura": sub,
            "distrito": sub, "logradouro": rua, "lat": lat, "lon": -46.6,
            "local_id": f"{grupo}|{lat}|-46.6", "data_abertura": pd.Timestamp(abertura), "dias_ate_resolver": dias}


def test_ct15_mesma_rua_e_tipo_viram_um_problema_com_contagem_de_pontos():
    s = pd.DataFrame([_p(1), _p(2, lat=-23.501), _p(3, rua="Rua B"), _p(4, grupo="Bueiro")])
    prob = open_problems(s).set_index("problema_id")
    a = prob.loc["SE|Buraco|RUA A"]
    assert a["pedidos_abertos"] == 2 and a["pontos"] == 2
    assert len(prob) == 3


def test_ct16_dias_de_espera_somam_todos_os_pedidos_abertos():
    s = pd.DataFrame([_p(1, abertura="2026-09-20"), _p(2, abertura="2026-09-25")])   # corte 30/09: 10 + 5
    lista = build_list(s)
    assert lista.iloc[0]["dias_de_espera"] == 15 and lista.iloc[0]["dias_em_aberto"] == 10


def test_ct17_ordem_e_comparacao_com_o_tempo_tipico():
    s = pd.DataFrame([
        _p(1, rua="Rua A", abertura="2026-09-20"),                       # 10 dias, 1 pedido
        _p(2, rua="Rua B", abertura="2026-07-02"),                       # 90 dias, 1 pedido
        _p(3, rua="Rua C", status="Finalizada", dias=3),                 # define o típico (3 dias)
        _p(4, rua="Rua C", status="Finalizada", dias=5),
    ])
    lista = build_list(s)
    assert lista["logradouro"].tolist() == ["Rua B", "Rua A"]
    assert lista.iloc[0]["mediana_tipica_dias"] == 4
    assert lista.iloc[0]["vezes_acima_do_tipico"] == pytest.approx(22.5)
    assert lista["posicao"].tolist() == [1, 2]
