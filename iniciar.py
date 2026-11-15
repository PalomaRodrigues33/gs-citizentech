"""Sobe o CitizenTech com um comando: dependências, dados, app compilado e API.

Uso:  python iniciar.py                 http://localhost:8000
      python iniciar.py --porta 8001
      python iniciar.py --rede          libera o acesso pelo celular na mesma rede Wi-Fi
"""
import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ / "web"
TOTAL = 4


def passo(n, texto):
    print(f"\n[{n}/{TOTAL}] {texto}", flush=True)


def rodar(cmd, cwd=None):
    """Executa um comando. No Windows, npm é um .cmd e precisa passar pelo shell."""
    if isinstance(cmd, str):
        subprocess.run(cmd, cwd=cwd, check=True, shell=True)
    else:
        subprocess.run(cmd, cwd=cwd, check=True)


def dependencias_instaladas() -> bool:
    try:
        import fastapi, openpyxl, pandas, sklearn, uvicorn  # noqa: F401
        return True
    except ImportError:
        return False


def dados_prontos() -> bool:
    from api.servicos import data_ready
    return data_ready()


def web_desatualizado() -> bool:
    indice = WEB / "dist" / "index.html"
    if not indice.exists():
        return True
    fontes = [f.stat().st_mtime for f in (WEB / "src").rglob("*") if f.is_file()]
    return bool(fontes) and max(fontes) > indice.stat().st_mtime


def porta_ocupada(porta: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0


def ip_da_rede() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "IP-DO-COMPUTADOR"


def main():
    ap = argparse.ArgumentParser(description="Sobe o CitizenTech inteiro com um comando.")
    ap.add_argument("--porta", type=int, default=8000)
    ap.add_argument("--rede", action="store_true", help="aceita acesso de outros aparelhos da rede")
    ap.add_argument("--refazer-dados", action="store_true", help="refaz o pipeline mesmo se já houver dados")
    args = ap.parse_args()

    os.chdir(RAIZ)

    passo(1, "Dependências do Python")
    if dependencias_instaladas() and not args.refazer_dados:
        print("    já instaladas.")
    else:
        rodar([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if not dependencias_instaladas():
        sys.exit("\nAs dependências não foram instaladas. Rode: python -m pip install -r requirements.txt")

    passo(2, "Dados do SP156 (camadas, modelo e banco)")
    if dados_prontos() and not args.refazer_dados:
        print("    já gerados; usando o que está em data/.")
    else:
        rodar([sys.executable, "run_all.py"])

    passo(3, "App React")
    if not web_desatualizado():
        print("    já compilado e atualizado.")
    elif shutil.which("npm") is None:
        print("    AVISO: npm não encontrado. A API vai subir, mas as telas não.")
        print("    Instale o Node 22 (nodejs.org) e rode de novo para ver o app.")
    else:
        if not (WEB / "node_modules").exists():
            print("    instalando as dependências do app (primeira vez, demora um pouco)...")
            rodar("npm install --no-audit --no-fund", cwd=WEB)
        rodar("npm run build", cwd=WEB)

    passo(4, "API e app")
    if porta_ocupada(args.porta):
        sys.exit(f"\nA porta {args.porta} já está em uso. Feche o outro servidor "
                 f"ou rode: python iniciar.py --porta {args.porta + 1}")

    host = "0.0.0.0" if args.rede else "127.0.0.1"
    print(f"    abra: http://localhost:{args.porta}")
    if args.rede:
        print(f"    no celular, na mesma rede Wi-Fi: http://{ip_da_rede()}:{args.porta}")
    print("    documentação da API: /docs      (Ctrl+C encerra)\n")

    import uvicorn
    uvicorn.run("api.main:app", host=host, port=args.porta)


if __name__ == "__main__":
    main()
