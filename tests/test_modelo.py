"""Testes do modelo de chance de resolução em 7 dias (CT-13 e CT-14)."""
import numpy as np
import pandas as pd

from ml.modelo import predict_risk, train_and_evaluate


def silver_sintetica(n=1200, seed=0):
    """Base com padrão aprendível: a subprefeitura LENTA resolve bem menos em 7 dias."""
    rng = np.random.default_rng(seed)
    sub = rng.choice(["LENTA", "RAPIDA"], size=n)
    grupo = rng.choice(["Buraco", "Varrição"], size=n)
    abertura = pd.Timestamp("2026-07-01") + pd.to_timedelta(rng.integers(0, 85, size=n), unit="D")
    resolvido = rng.binomial(1, np.where(sub == "LENTA", 0.2, 0.9)).astype(float)
    return pd.DataFrame({
        "pedido_id": np.arange(1, n + 1), "grupo": grupo, "servico": grupo, "status": "Finalizada",
        "data_abertura": abertura, "resolvido_7d": resolvido, "subprefeitura": sub, "distrito": sub,
        "pedidos_no_local": 1, "dia_semana": abertura.dayofweek})


def test_ct13_modelo_supera_a_regra_do_grupo_com_corte_temporal():
    _, m = train_and_evaluate(silver_sintetica(), treino_corte="2026-08-31")
    assert m["depois_com_ia"]["auc"] > 0.8 > m["antes_sem_ia"]["auc"]
    assert m["treino"]["pedidos"] + m["teste"]["pedidos"] == 1200
    assert all(v == 0.5 for v in m["antes_sem_ia"]["auc_dentro_de_cada_grupo"].values())


def test_ct14_risco_maior_na_regiao_lenta_e_entre_0_e_1():
    s = silver_sintetica()
    model, _ = train_and_evaluate(s)
    occ = s.head(60)
    r = predict_risk(model, occ)
    lenta = (occ["subprefeitura"] == "LENTA").to_numpy()
    assert r[lenta].mean() > r[~lenta].mean() + 0.3
    assert r.between(0, 1).all()
