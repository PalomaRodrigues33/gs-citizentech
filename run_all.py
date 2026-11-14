"""Fluxo completo: raw -> bronze -> silver -> modelo -> atrasos -> análises -> banco.

Uso:  python run_all.py              reaproveita a bronze existente
      python run_all.py --reingerir  relê o arquivo do SP156 (cerca de 35 s)
"""
import argparse
import pickle

import config as cfg
from analytics.run import run_queries
from ingestion.sp156 import BRONZE_FILE, run_ingestion
from ml.modelo import save_metrics, train_and_evaluate
from pipeline.gold import write_gold
from pipeline.silver import run_silver
from transparencia.atrasos import build_list

TOTAL = 5


def main(reingerir: bool = False):
    print(f"1/{TOTAL} Ingestão do SP156 (raw -> bronze)...")
    if reingerir or not (cfg.BRONZE_DIR / BRONZE_FILE).exists():
        _, rep = run_ingestion()
        print(f"    {rep['linhas_lidas']} linhas lidas; {rep['linhas_no_recorte']} nos 5 grupos de zeladoria")
    else:
        print("    bronze já existe (use --reingerir para refazer)")

    print(f"2/{TOTAL} Limpeza (bronze -> silver -> banco)...")
    silver, quality = run_silver()
    print(quality.to_string(index=False))

    print(f"3/{TOTAL} IA: chance de resolução em 7 dias (treina jul-ago, avalia set)...")
    model, metrics = train_and_evaluate(silver)
    save_metrics(metrics)
    with open(cfg.MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    a, d = metrics["antes_sem_ia"], metrics["depois_com_ia"]
    print(f"    antes (taxa do grupo): AUC {a['auc']} | depois (modelo): AUC {d['auc']}")
    print(f"    AUC dentro de cada grupo (antes = 0,5): {d['auc_dentro_de_cada_grupo']}")

    print(f"4/{TOTAL} Lista pública de atrasos (dias de espera somados dos pedidos abertos)...")
    atrasos = build_list(silver)
    write_gold(atrasos)
    cols = ["posicao", "grupo", "subprefeitura", "pedidos_abertos", "dias_em_aberto", "mediana_tipica_dias",
            "dias_de_espera"]
    print(atrasos[cols].head(5).to_string(index=False))

    print(f"5/{TOTAL} Consultas analíticas (funções de janela)...")
    for nome, df in run_queries().items():
        print(f"    {nome}: {len(df)} linhas")

    print(f"\nBanco: {cfg.DB_PATH}\nGold:  {cfg.GOLD_DIR}")
    print("App:   python -m uvicorn api.main:app --port 8000   (veja o README)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reingerir", action="store_true")
    try:
        main(ap.parse_args().reingerir)
    except FileNotFoundError as exc:          # arquivo do SP156 ausente: mensagem clara, sem traceback
        raise SystemExit(f"\n{exc}")
