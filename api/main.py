"""API do CitizenTech (FastAPI). Também serve o app React compilado (web/dist) na raiz."""
import sys
import time
from collections import defaultdict, deque
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import config as cfg
from api import servicos
from api.validacao import PedidoAssistente, validate_group, validate_region
from ia.llm import get_llm

app = FastAPI(title="ZeladoriaSP API", version="2.0",
              description="Assistente do cidadão para o SP156 e transparência da zeladoria em São Paulo.")
app.add_middleware(CORSMiddleware, allow_origins=cfg.CORS_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["content-type"])

CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
        resp.headers["Content-Security-Policy"] = CSP
    return resp


class RateLimiter:
    """Janela deslizante em memória: no máximo `limite` chamadas por `janela_s` segundos por chave."""

    def __init__(self, limite: int, janela_s: float = 60.0):
        self.limite, self.janela_s = limite, janela_s
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, chave: str, agora: float | None = None) -> bool:
        agora = time.monotonic() if agora is None else agora
        q = self._hits[chave]
        while q and agora - q[0] > self.janela_s:
            q.popleft()
        if len(q) >= self.limite:
            return False
        q.append(agora)
        return True


limiter = RateLimiter(cfg.LIMITE_ASSISTENTE_POR_MIN)


@lru_cache(maxsize=1)
def llm():
    return get_llm()


def _require_data():
    if not servicos.data_ready():
        raise HTTPException(503, "Dados ainda não gerados. Rode `python run_all.py` (veja o README).")


def _check(*erros):
    for e in erros:
        if e:
            raise HTTPException(422, e)


@app.get("/api/saude")
def saude():
    return {"ok": True, "dados_prontos": servicos.data_ready(), "provedor_ia": llm().name}


@app.get("/api/regioes")
def regioes():
    _require_data()
    return {"subprefeituras": servicos.regions(), "grupos": list(cfg.GRUPOS)}


@app.get("/api/regiao")
def regiao(subprefeitura: str = Query(..., max_length=80), grupo: str | None = Query(None, max_length=60)):
    _require_data()
    _check(validate_region(subprefeitura, None, servicos.regions()), validate_group(grupo))
    return servicos.region_summary(subprefeitura, grupo)


@app.get("/api/atrasos")
def atrasos(subprefeitura: str | None = Query(None, max_length=80), grupo: str | None = Query(None, max_length=60),
            limite: int = Query(20, ge=1, le=100)):
    _require_data()
    _check(validate_region(subprefeitura, None, servicos.regions()), validate_group(grupo))
    return servicos.delays(subprefeitura, grupo, limite)


@app.post("/api/assistente")
def assistente(pedido: PedidoAssistente, request: Request):
    _require_data()
    _check(validate_region(pedido.subprefeitura, pedido.distrito, servicos.regions()))
    ip = request.client.host if request.client else "desconhecido"
    if not limiter.allow(ip):
        raise HTTPException(429, "Muitas solicitações em pouco tempo. Aguarde um minuto e tente de novo.")
    return servicos.prepare_request(pedido.texto, pedido.subprefeitura, pedido.distrito, llm())


@app.get("/api/canais")
def canais():
    return {"canais": cfg.CANAIS, "checklist": cfg.CHECKLIST, "emergencia": cfg.EMERGENCIA}


@app.get("/api/sobre")
def sobre():
    return servicos.about()


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    return JSONResponse({"erro": exc.detail}, status_code=exc.status_code)


# App React compilado (npm run build). Montado por último para não encobrir a API.
if cfg.WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=cfg.WEB_DIST, html=True), name="web")
