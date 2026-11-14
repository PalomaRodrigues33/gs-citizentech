"""Teste rápido do provedor de LLM.

Uso:  python -m ia.smoke             prepara uma solicitação de teste
      python -m ia.smoke --modelos   lista os modelos da sua chave
"""
import json
import sys

from ia.assistente import assist
from ia.llm import get_llm


def main():
    llm = get_llm()
    if "--modelos" in sys.argv:
        if not hasattr(llm, "listar_modelos"):
            print(f"{llm.name} não expõe lista de modelos")
            return
        print("\n".join(llm.listar_modelos()))
        return
    print(f"Provedor: {llm.name}")
    r = assist("tem um buraco enorme na Rua Tabapuã há duas semanas, perto da padaria", llm)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r["erro"]:
        print(">>> A chamada falhou; confira a chave e o modelo.")


if __name__ == "__main__":
    main()
