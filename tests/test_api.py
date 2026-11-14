"""Testes da API (CT-29 a CT-37). Usam os dados gerados por `python run_all.py`; sem eles, são ignorados."""
import pytest
from fastapi.testclient import TestClient

import config as cfg
from api import main
from api.servicos import data_ready

pytestmark = pytest.mark.skipif(not data_ready(), reason="requer os dados gerados (python run_all.py)")


@pytest.fixture(scope="module")
def c():
    return TestClient(main.app)


@pytest.fixture
def regiao(c):
    subs = c.get("/api/regioes").json()["subprefeituras"]
    sub = "MOOCA" if "MOOCA" in subs else next(iter(subs))
    return sub, subs[sub][0]


def test_ct29_saude_e_regioes(c):
    assert c.get("/api/saude").json()["dados_prontos"] is True
    r = c.get("/api/regioes").json()
    assert len(r["subprefeituras"]) >= 30 and r["grupos"] == list(cfg.GRUPOS)


def test_ct30_regiao_responde_tres_perguntas_com_frase(c, regiao):
    r = c.get("/api/regiao", params={"subprefeitura": regiao[0]}).json()
    assert [q["id"] for q in r["perguntas"]] == ["tempo", "tendencia", "comparacao"]
    assert all(len(q["resposta"]) > 20 for q in r["perguntas"])
    assert 0 <= r["resumo"]["resolvidos_7d_pct"] <= 100


def test_ct31_filtros_invalidos_sao_recusados(c):
    assert c.get("/api/regiao", params={"subprefeitura": "NARNIA"}).status_code == 422
    assert c.get("/api/regiao", params={"subprefeitura": "MOOCA", "grupo": "Iluminação"}).status_code == 422
    assert c.get("/api/atrasos", params={"limite": 1000}).status_code == 422
    assert c.get("/api/regiao", params={"subprefeitura": "x' OR 1=1 --"}).json()["erro"] == "Subprefeitura desconhecida."


def test_ct32_atrasos_ordenados(c, regiao):
    r = c.get("/api/atrasos", params={"subprefeitura": regiao[0], "limite": 10}).json()
    esperas = [i["dias_de_espera"] for i in r["itens"]]
    assert esperas == sorted(esperas, reverse=True) and r["data_referencia"] == cfg.DATA_CORTE


def test_ct33_assistente_prepara_pedido_com_canais_oficiais(c, regiao):
    r = c.post("/api/assistente", json={"texto": "tem um buraco enorme na Rua da Mooca há uma semana",
                                         "subprefeitura": regiao[0], "distrito": regiao[1]}).json()
    assert r["servico"] in cfg.SERVICOS and 0 <= r["chance_7d_pct"] <= 100
    assert r["canais"] == cfg.CANAIS and r["contexto"]["pedidos_trimestre"] >= 0


def test_ct34_assistente_valida_texto_e_regiao(c, regiao):
    curto = c.post("/api/assistente", json={"texto": "oi", "subprefeitura": regiao[0], "distrito": regiao[1]})
    assert curto.status_code == 422
    longo = c.post("/api/assistente", json={"texto": "x" * 501, "subprefeitura": regiao[0], "distrito": regiao[1]})
    assert longo.status_code == 422
    errado = c.post("/api/assistente", json={"texto": "buraco grande na rua", "subprefeitura": regiao[0], "distrito": "NARNIA"})
    assert errado.status_code == 422 and "Distrito" in errado.json()["erro"]


def test_ct35_fora_da_zeladoria_nao_inventa_previsao(c, regiao):
    r = c.post("/api/assistente", json={"texto": "o semáforo da avenida está apagado desde ontem",
                                         "subprefeitura": regiao[0], "distrito": regiao[1]}).json()
    assert r["servico"] == "outro" and r["chance_7d_pct"] is None and r["contexto"] is None


def test_ct36_limite_de_chamadas_por_ip():
    lim = main.RateLimiter(limite=3, janela_s=60)
    assert [lim.allow("ip", agora=t) for t in (0, 1, 2, 3)] == [True, True, True, False]
    assert lim.allow("outro-ip", agora=3) is True
    assert lim.allow("ip", agora=61.5) is True                         # a janela andou


def test_ct37_cabecalhos_de_seguranca(c):
    h = c.get("/api/saude").headers
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    assert "default-src 'self'" in h["content-security-policy"]
