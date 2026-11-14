"""Regras da API: indicadores da região (com a resposta em uma frase), lista de atrasos e assistente."""
import json
import pickle
import sqlite3
from contextlib import closing
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

import config as cfg
from analytics.run import run
from ia.assistente import assist, log_example
from ml.modelo import predict_risk


def connect(db_path=None) -> sqlite3.Connection:
    return sqlite3.connect(db_path or cfg.DB_PATH)


def data_ready(db_path=None) -> bool:
    try:
        with closing(connect(db_path)) as con:
            names = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    except sqlite3.Error:
        return False
    return {"pedidos", "lista_atrasos"} <= names and Path(cfg.MODEL_PATH).exists()


@lru_cache(maxsize=1)
def regions(db_path=None) -> dict[str, list[str]]:
    with closing(connect(db_path)) as con:
        df = pd.read_sql("select distinct subprefeitura, distrito from pedidos "
                         "where subprefeitura is not null and distrito is not null "
                         "and subprefeitura not like '%nao encontrada%'", con)
    return {s: sorted(g["distrito"]) for s, g in sorted(df.groupby("subprefeitura"))}


@lru_cache(maxsize=1)
def model():
    with open(cfg.MODEL_PATH, "rb") as f:
        return pickle.load(f)


def _pct(x):
    return None if x is None or pd.isna(x) else round(float(x), 1)


def _pontos(delta: float) -> str:
    d = round(delta)
    if d == 0:
        return "praticamente igual"
    return f"{'+' if d > 0 else '−'}{abs(d)} ponto{'s' if abs(d) != 1 else ''} percentua{'is' if abs(d) != 1 else 'l'}"


def _ordinal(n: int) -> str:
    return f"{n}ª"


# ------------------------------------------------------------------ Meu bairro
def region_summary(subprefeitura: str, grupo: str | None = None, db_path=None) -> dict:
    """Indicadores e três perguntas do cidadão, cada uma com a resposta em uma frase."""
    with closing(connect(db_path)) as con:
        params = {"s": subprefeitura, "g": grupo}
        head = pd.read_sql(
            "select count(*) pedidos, "
            "sum(case when status in ('Aberto','Em Andamento') then 1 else 0 end) abertos, "
            "avg(resolvido_7d) taxa from pedidos where subprefeitura = :s and (:g is null or grupo = :g)",
            con, params=params).iloc[0]
        cidade = pd.read_sql("select avg(resolvido_7d) taxa from pedidos where (:g is null or grupo = :g)",
                             con, params=params).iloc[0]
        tempo = run(con, "tempo_por_tipo", subprefeitura=subprefeitura)
        tend = run(con, "tendencia_semanal", subprefeitura=subprefeitura, grupo=grupo)
        rank = run(con, "ranking_regioes", grupo=grupo)

    resumo = {"pedidos": int(head["pedidos"]), "abertos": int(head["abertos"] or 0),
              "resolvidos_7d_pct": _pct(100 * head["taxa"]) if head["taxa"] is not None else None,
              "cidade_resolvidos_7d_pct": _pct(100 * cidade["taxa"]) if cidade["taxa"] is not None else None}
    return {"subprefeitura": subprefeitura, "grupo": grupo, "resumo": resumo,
            "perguntas": [_q_tempo(tempo, grupo), _q_tendencia(tend, grupo), _q_comparacao(rank, subprefeitura, grupo)]}


def _q_tempo(tempo: pd.DataFrame, grupo):
    reg = tempo[tempo["escopo"] == "regiao"].set_index("grupo")
    cid = tempo[tempo["escopo"] == "cidade"].set_index("grupo")
    dados = []
    for g in cid.index:
        r = reg.loc[g] if g in reg.index else None
        dados.append({"grupo": g,
                      "regiao_pct": None if r is None else _pct(r["resolvidos_7d_pct"]),
                      "cidade_pct": _pct(cid.loc[g, "resolvidos_7d_pct"]),
                      "regiao_mediana_dias": None if r is None else _pct(r["mediana_dias"]),
                      "pedidos_regiao": 0 if r is None else int(r["pedidos"])})
    dados.sort(key=lambda d: (d["regiao_pct"] is None, d["regiao_pct"] if d["regiao_pct"] is not None else 0))
    validos = [d for d in dados if d["regiao_pct"] is not None and d["pedidos_regiao"] >= 20]
    foco = next((d for d in validos if d["grupo"] == grupo), None) if grupo else (validos[0] if validos else None)
    if foco is None:
        resposta = "Há poucos pedidos desse tipo na região para uma estimativa confiável."
    else:
        dif = foco["regiao_pct"] - foco["cidade_pct"]
        comp = ("acima da média da cidade" if dif >= 3 else "abaixo da média da cidade" if dif <= -3
                else "parecido com a média da cidade")
        med = foco["regiao_mediana_dias"]
        prefixo = f"{foco['grupo']}: " if grupo else f"O mais lento aqui é {foco['grupo'].lower()}: "
        resposta = (f"{prefixo}{foco['regiao_pct']:.0f}% resolvidos em até 7 dias, {comp} "
                    f"({foco['cidade_pct']:.0f}%). Metade leva até {med:.0f} dia{'s' if med != 1 else ''}.")
    return {"id": "tempo", "pergunta": "Quanto tempo cada tipo de problema leva aqui?", "resposta": resposta,
            "destaque": foco["grupo"] if foco else None, "dados": dados}


def _q_tendencia(tend: pd.DataFrame, grupo):
    t = tend.dropna(subset=["regiao_media_3sem"])
    dados = [{"semana": r["semana"], "inicio": r["inicio"], "regiao_pct": _pct(r["regiao_media_3sem"]),
              "cidade_pct": _pct(r["cidade_media_3sem"]), "pedidos": int(r["n_regiao"])}
             for _, r in tend.iterrows()]
    if len(t) < 3 or t["n_regiao"].sum() < 60:
        resposta = "Há poucos pedidos na região para medir a tendência com segurança."
    else:
        ini, fim = t.iloc[2] if len(t) > 2 else t.iloc[0], t.iloc[-1]   # 1º ponto com 3 semanas completas
        delta = fim["regiao_media_3sem"] - ini["regiao_media_3sem"]
        rumo = ("melhorou" if delta >= 3 else "piorou" if delta <= -3 else "ficou estável")
        resposta = (f"{rumo.capitalize()}: {fim['regiao_media_3sem']:.0f}% resolvidos em 7 dias nas últimas "
                    f"3 semanas, contra {ini['regiao_media_3sem']:.0f}% no fim de julho ({_pontos(delta)}).")
    return {"id": "tendencia", "pergunta": "A sua região está melhorando ou piorando?", "resposta": resposta,
            "nota": "Média móvel de 3 semanas, de 13/07 a 23/09. As duas primeiras semanas de julho ficaram de fora: nelas os prazos subiram em todos os tipos e na cidade inteira ao mesmo tempo, o que indica mudança na operação ou no registro, e não no seu bairro.",
            "dados": dados}


def _q_comparacao(rank: pd.DataFrame, subprefeitura, grupo):
    dados = [{"posicao": int(r["posicao"]), "terco": int(r["terco"]), "subprefeitura": r["subprefeitura"],
              "resolvidos_7d_pct": _pct(r["resolvidos_7d_pct"]), "pedidos": int(r["pedidos"])}
             for _, r in rank.iterrows()]
    me = next((d for d in dados if d["subprefeitura"] == subprefeitura), None)
    total = len(dados)
    if me is None:
        resposta = "A região tem poucos pedidos desse tipo para entrar na comparação."
    else:
        tipo = f" em {grupo.lower()}" if grupo else ""
        terco = {1: "entre as mais rápidas", 2: "no meio da tabela", 3: "entre as mais lentas"}[me["terco"]]
        resposta = (f"{_ordinal(me['posicao'])} de {total} subprefeituras{tipo}: {terco} para resolver "
                    f"em até 7 dias.")
    return {"id": "comparacao", "pergunta": "Como a sua região se compara às outras?", "resposta": resposta,
            "destaque": subprefeitura, "dados": dados}


# ------------------------------------------------------------------ Atrasos
def delays(subprefeitura=None, grupo=None, limite=20, db_path=None) -> dict:
    with closing(connect(db_path)) as con:
        df = run(con, "atrasos", subprefeitura=subprefeitura, grupo=grupo, limite=limite)
        tot = pd.read_sql("select count(*) n, coalesce(sum(pedidos_abertos),0) p from lista_atrasos "
                          "where (:s is null or subprefeitura = :s) and (:g is null or grupo = :g)",
                          con, params={"s": subprefeitura, "g": grupo}).iloc[0]
    itens = json.loads(df.to_json(orient="records", force_ascii=False))
    return {"data_referencia": cfg.DATA_CORTE, "problemas_abertos": int(tot["n"]), "pedidos_abertos": int(tot["p"]),
            "itens": itens}


# ------------------------------------------------------------------ Assistente
def local_context(servico: str, subprefeitura: str, distrito: str, db_path=None) -> dict:
    """O que os dados reais dizem sobre esse serviço no distrito (ou na subprefeitura, se houver poucos)."""
    with closing(connect(db_path)) as con:
        q = ("select count(*) pedidos, avg(resolvido_7d) taxa, "
             "sum(case when status in ('Aberto','Em Andamento') then 1 else 0 end) abertos "
             "from pedidos where servico = :sv and {col} = :v")
        d = pd.read_sql(q.format(col="distrito"), con, params={"sv": servico, "v": distrito}).iloc[0]
        escopo, nome = "distrito", distrito
        if d["pedidos"] < cfg.MIN_PEDIDOS_DISTRITO:
            d = pd.read_sql(q.format(col="subprefeitura"), con, params={"sv": servico, "v": subprefeitura}).iloc[0]
            escopo, nome = "subprefeitura", subprefeitura
        med = pd.read_sql(f"select dias_ate_resolver from pedidos where servico = :sv and {escopo} = :v "
                          f"and dias_ate_resolver is not null", con, params={"sv": servico, "v": nome})
    return {"escopo": escopo, "local": nome, "pedidos_trimestre": int(d["pedidos"]),
            "abertos": int(d["abertos"] or 0),
            "mediana_dias": None if med.empty else float(med["dias_ate_resolver"].median()),
            "historico_7d_pct": None if d["taxa"] is None or pd.isna(d["taxa"]) else round(100 * float(d["taxa"]), 1)}


def prepare_request(texto, subprefeitura, distrito, llm, log=True, db_path=None) -> dict:
    r = assist(texto, llm)
    out = {**r, "checklist": cfg.CHECKLIST, "canais": cfg.CANAIS,
           "emergencia": cfg.EMERGENCIA if r["risco_imediato"] else None,
           "contexto": None, "chance_7d_pct": None}
    if r["servico"] != "outro":
        feats = pd.DataFrame([{"grupo": r["grupo"], "servico": r["servico"], "subprefeitura": subprefeitura,
                               "distrito": distrito, "dia_semana": date.today().weekday(), "pedidos_no_local": 1}])
        out["chance_7d_pct"] = round(100 * (1 - float(predict_risk(model(), feats).iloc[0])), 0)
        out["contexto"] = local_context(r["servico"], subprefeitura, distrito, db_path)
    if log and cfg.LOG_EXEMPLOS:
        log_example(texto, {k: out[k] for k in ("servico", "resumo", "texto_solicitacao", "informacoes_faltando",
                                                "risco_imediato", "confianca", "provedor", "erro", "chance_7d_pct")})
    return out


def about() -> dict:
    p = Path(cfg.GOLD_DIR)
    m = json.loads((p / "metricas_ia.json").read_text(encoding="utf-8")) if (p / "metricas_ia.json").exists() else None
    a = p / "metricas_assistente.json"
    ma = json.loads(a.read_text(encoding="utf-8")) if a.exists() else None
    if ma:
        ma = {k: v for k, v in ma.items() if not k.startswith("detalhes")}
    return {"fonte": {"nome": "SP156 - Solicitações (Prefeitura de São Paulo, dados abertos)",
                      "url": "https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156",
                      "periodo": "01/07/2026 a 30/09/2026"},
            "modelo_7_dias": m, "assistente": ma, "canais": cfg.CANAIS}
