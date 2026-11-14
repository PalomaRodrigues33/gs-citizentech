"""Mede o assistente no conjunto rotulado: antes (palavras-chave) x depois (LLM).

Uso:  python -m ia.avaliacao
"""
import json
from pathlib import Path

import config as cfg
from ia.assistente import assist
from ia.llm import MockLLM, get_llm
from ia.rotulados import ROTULADOS


def accuracy(llm, verbose=False) -> dict:
    exato = grupo = erros = 0
    detalhes = []
    for texto, esperado in ROTULADOS:
        r = assist(texto, llm)
        ok = r["servico"] == esperado
        ok_g = cfg.SERVICOS.get(r["servico"]) == cfg.SERVICOS.get(esperado)
        exato += ok
        grupo += ok_g
        erros += bool(r["erro"])
        detalhes.append({"relato": texto, "esperado": esperado, "obtido": r["servico"], "acertou": bool(ok)})
        if verbose:
            print(f"  {'ok ' if ok else 'ERR'} {esperado[:40]:40s} -> {r['servico'][:40]}")
    n = len(ROTULADOS)
    return {"provedor": llm.name, "casos": n, "acertos_servico": exato, "acuracia_servico": round(exato / n, 3),
            "acuracia_grupo": round(grupo / n, 3), "erros_de_chamada": erros, "detalhes": detalhes}


def main():
    base = accuracy(MockLLM())
    resumo = lambda d: {k: v for k, v in d.items() if k != "detalhes"}
    out = {"pergunta": "A IA leva o relato livre do cidadão ao serviço EXATO do SP156?",
           "antes_sem_ia": {"descricao": "regras de palavras-chave", **resumo(base)},
           "detalhes_antes": base["detalhes"]}
    llm = get_llm()
    if llm.name != base["provedor"]:
        print(f"Avaliando {llm.name} em {len(ROTULADOS)} relatos...")
        depois = accuracy(llm, verbose=True)
        out["depois_com_ia"] = {"descricao": "LLM com prompt de papel, regras e few-shot", **resumo(depois)}
        out["detalhes_depois"] = depois["detalhes"]
    else:
        out["nota"] = ("Provedor mock: só a linha de base foi medida. Defina LLM_PROVIDER e a chave "
                       "(veja docs/ia.md) e rode de novo para medir o LLM.")
    cfg.GOLD_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(cfg.GOLD_DIR) / "metricas_assistente.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("detalhes")}, ensure_ascii=False, indent=2))
    print(f"\nGravado em {path}")


if __name__ == "__main__":
    main()
