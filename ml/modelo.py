"""IA: chance de um pedido ser resolvido em até 7 dias (gradient boosting, corte temporal)."""
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

import config as cfg

CAT = ["grupo", "servico", "subprefeitura", "distrito"]
NUM = ["dia_semana", "apoios_no_local"]
FEATURES = CAT + NUM


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ("subprefeitura", "distrito"):
        d[c] = d[c].fillna("DESCONHECIDA")
    d["apoios_no_local"] = (d["pedidos_no_local"] - 1).clip(lower=0)
    return d


def _pipeline() -> Pipeline:
    enc = ColumnTransformer([("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CAT)],
                            remainder="passthrough")
    clf = HistGradientBoostingClassifier(random_state=cfg.SEED, categorical_features=list(range(len(CAT))))
    return Pipeline([("prep", enc), ("clf", clf)])


def train_and_evaluate(silver: pd.DataFrame, treino_corte=None):
    """Treina em jul-ago, avalia em setembro e re-treina com tudo. Retorna (modelo_final, metricas)."""
    corte = pd.Timestamp(treino_corte or cfg.TREINO_CORTE)
    known = _prep(silver[silver["resolvido_7d"].notna()])
    tr = known[known["data_abertura"] <= corte]
    te = known[known["data_abertura"] > corte]
    model = _pipeline().fit(tr[FEATURES], tr["resolvido_7d"])
    p = model.predict_proba(te[FEATURES])[:, 1]
    taxa_grupo = tr.groupby("grupo")["resolvido_7d"].mean()
    base = te["grupo"].map(taxa_grupo).fillna(tr["resolvido_7d"].mean()).to_numpy()
    y = te["resolvido_7d"].to_numpy()

    def _por_grupo(score):
        out = {}
        for g in sorted(known["grupo"].unique()):
            m = (te["grupo"] == g).to_numpy()
            if m.sum() >= 50 and len(set(y[m])) > 1:
                out[g] = round(float(roc_auc_score(y[m], np.asarray(score)[m])), 3)
        return out

    metrics = {
        "pergunta": "Este pedido será resolvido em até 7 dias?",
        "treino": {"periodo": f"{tr['data_abertura'].min():%d/%m} a {corte:%d/%m}", "pedidos": int(len(tr))},
        "teste": {"periodo": f"{corte + pd.Timedelta(days=1):%d/%m} em diante (setembro)", "pedidos": int(len(te)),
                  "taxa_real_7d": round(float(y.mean()), 3)},
        "antes_sem_ia": {
            "descricao": "taxa histórica do tipo de serviço (regra simples, sem modelo)",
            "auc": round(float(roc_auc_score(y, base)), 3),
            "brier": round(float(brier_score_loss(y, base)), 4),
            "auc_dentro_de_cada_grupo": {g: 0.5 for g in _por_grupo(p)},
        },
        "depois_com_ia": {
            "descricao": "gradient boosting (grupo, serviço, subprefeitura, distrito, dia da semana, apoios no local)",
            "auc": round(float(roc_auc_score(y, p)), 3),
            "brier": round(float(brier_score_loss(y, p)), 4),
            "auc_dentro_de_cada_grupo": _por_grupo(p),
        },
        "leitura": "AUC mede a capacidade de ordenar o risco (0,5 = chute; 1 = perfeito); Brier mede o erro da "
                   "probabilidade (menor é melhor). O ganho decisivo é DENTRO de cada grupo: a regra simples "
                   "não distingue dois buracos (AUC 0,5); o modelo distingue pelo local e pelo contexto.",
        "ressalva": "Modelo treinado com 2 meses do SP156 real e avaliado em 1 mês; a previsão é um apoio à "
                    "gestão, não um compromisso de prazo.",
    }
    final = _pipeline().fit(known[FEATURES], known["resolvido_7d"])
    return final, metrics


def predict_risk(model, occ: pd.DataFrame) -> pd.Series:
    d = _prep(occ)
    return pd.Series(1 - model.predict_proba(d[FEATURES])[:, 1], index=occ.index).round(3)


def save_metrics(metrics: dict, gold_dir: Path | None = None):
    gold_dir = Path(gold_dir or cfg.GOLD_DIR)
    gold_dir.mkdir(parents=True, exist_ok=True)
    (gold_dir / "metricas_ia.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
