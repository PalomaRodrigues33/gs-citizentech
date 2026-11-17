"""Provedores de LLM com a mesma interface: complete(system, messages) -> texto.

Escolha pela variável LLM_PROVIDER: mock (offline, sem chave), groq, gemini, openai_compat, anthropic.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

import config as cfg


def _http_error(exc: urllib.error.HTTPError) -> RuntimeError:
    """Erro legível: status HTTP e a explicação devolvida pela API (sem a chave)."""
    try:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
    except Exception:
        detail = ""
    return RuntimeError(f"HTTP {exc.code}: {detail or exc.reason}")


class MockLLM:
    """Regras de palavras-chave. Não é IA generativa: é a linha de base e o modo offline."""

    name = "mock-regras"

    # (palavras, serviço) — a ordem importa: o mais específico primeiro
    REGRAS = (
        (("corredor de ônibus", "corredor de onibus", "faixa exclusiva", "faixa de ônibus"),
         "Tapa-buraco em faixa exclusiva ou corredor de ônibus"),
        (("buraco", "cratera", "asfalto", "recape"), "Tapa-buraco"),
        (("bueiro", "boca de lobo", "alag", "galeria", "poço de visita"),
         "Solicitar limpeza de bueiros, boca de lobo e poços de visita"),
        (("caçamba", "cacamba"), "Denunciar caçamba irregular de entulho de construção"),
        (("jogaram", "jogam", "ponto viciado", "descarte", "despejaram", "terreno baldio"),
         "Denunciar descarte irregular de entulho e outros resíduos em área pública"),
        (("sofá", "sofa", "colchão", "colchao", "móveis", "moveis", "entulho", "geladeira", "fogão", "madeira",
          "restos de poda", "lixo"), "Entulho e grandes objetos em via pública - solicitar remoção"),
        (("sacos da varrição", "sacos de varrição", "saco da varrição"),
         "Sacos de varrição - Fazer reclamação de falta de remoção"),
        (("varri", "varre", "gari", "folhas"), "Fazer reclamação de falta de varrição"),
        (("rebaixamento irregular", "rebaixaram a guia", "guia rebaixada irregular"),
         "Guia rebaixada - solicitar fiscalização de rebaixamento irregular"),
        (("rampa", "travessia", "guia rebaixada", "rebaixar a guia"),
         "Guias para travessia de pedestres - Solicitar rebaixamento"),
        (("não tem calçada", "nao tem calcada", "sem calçada", "sem calcada"),
         "Sugerir construção de calçadas em áreas públicas e praças"),
        (("cadeirante", "cadeira de rodas", "andador", "obstáculo", "obstaculo", "carrinho de bebê",
          "carrinho de bebe", "piso tátil", "poste no meio"),
         "Acessibilidade - solicitar avaliação de obstáculo na calçada"),
        (("praça", "praca", "escola", "posto de saúde", "ubs", "parque", "prédio público"),
         "Calçada pública - solicitar manutenção"),
        (("calçada", "calcada", "passeio"),
         "Calçada particular - denunciar calçada danificada ou inexistente"),
    )

    # Primeira frase do pedido, por serviço: diz o que está sendo pedido antes de descrever o problema.
    ABERTURA = {
        "Tapa-buraco": "Solicito o reparo de buraco no asfalto da via.",
        "Tapa-buraco em faixa exclusiva ou corredor de ônibus":
            "Solicito o reparo de buraco no asfalto em faixa exclusiva ou corredor de ônibus.",
        "Calçada pública - solicitar manutenção": "Solicito a manutenção de calçada pública danificada.",
        "Calçada particular - denunciar calçada danificada ou inexistente":
            "Venho denunciar calçada danificada em frente a imóvel particular e solicitar a fiscalização do responsável.",
        "Acessibilidade - solicitar avaliação de obstáculo na calçada":
            "Solicito a avaliação de obstáculo na calçada que impede a passagem de pedestres.",
        "Guias para travessia de pedestres - Solicitar rebaixamento":
            "Solicito o rebaixamento de guia para travessia de pedestres.",
        "Guia rebaixada - solicitar fiscalização de rebaixamento irregular":
            "Solicito a fiscalização de rebaixamento de guia feito de forma irregular.",
        "Sugerir construção de calçadas em áreas públicas e praças":
            "Sugiro a construção de calçada em área pública.",
        "Entulho e grandes objetos em via pública - solicitar remoção":
            "Solicito a remoção de entulho e objetos grandes deixados em via pública.",
        "Denunciar descarte irregular de entulho e outros resíduos em área pública":
            "Venho denunciar descarte irregular de entulho e outros resíduos em área pública.",
        "Denunciar caçamba irregular de entulho de construção":
            "Venho denunciar caçamba de entulho de construção em situação irregular.",
        "Solicitar limpeza de bueiros, boca de lobo e poços de visita":
            "Solicito a limpeza de bueiro, boca de lobo ou poço de visita.",
        "Fazer reclamação de falta de varrição": "Venho reclamar da falta de varrição na via.",
        "Sacos de varrição - Fazer reclamação de falta de remoção":
            "Venho reclamar da falta de remoção dos sacos de varrição.",
        "outro": "Solicito atendimento para o problema descrito abaixo.",
    }

    def complete(self, system: str, messages: list[dict]) -> str:
        msg = messages[-1]["content"]
        m = re.search(r"<relato>(.*?)</relato>", msg, re.DOTALL)
        relato = " ".join((m.group(1) if m else msg).split())
        low = relato.lower()
        servico = "outro"
        for chaves, s in self.REGRAS:
            if any(c in low for c in chaves):
                servico = s
                break
        faltando = []
        if not re.search(r"\b(rua|r\.|avenida|av\.|alameda|travessa|praça|estrada)\b", low):
            faltando.append("Endereço completo")
        if not re.search(r"\b(perto|em frente|ao lado|esquina|próximo|proximo)\b", low):
            faltando.append("Ponto de referência")
        if not re.search(r"\b(dia|dias|semana|semanas|mês|meses|desde|ontem)\b", low):
            faltando.append("Desde quando o problema existe")
        faltando.append("Foto nítida do local")
        # Uma linha por informação: é assim que o atendente do SP156 lê o campo de descrição.
        descricao = relato.rstrip(" .")
        linhas = [self.ABERTURA.get(servico, self.ABERTURA["outro"]), "", "Descrição: " + descricao[:1].upper() + descricao[1:] + "."]
        if "Endereço completo" in faltando:
            linhas.append("Endereço: [endereço completo, com número]")
        if "Ponto de referência" in faltando:
            linhas.append("Ponto de referência: [ponto de referência]")
        if "Desde quando o problema existe" in faltando:
            linhas.append("Desde quando: [desde quando o problema existe]")
        linhas += ["", "Agradeço a atenção."]
        texto = '\n'.join(linhas)
        return json.dumps({"servico": servico, "resumo": relato[:140], "texto_solicitacao": texto[:700],
                           "informacoes_faltando": faltando, "risco_imediato": False,
                           "confianca": "media"}, ensure_ascii=False)


class AnthropicLLM:
    """Cliente mínimo da API de mensagens (sem SDK, só biblioteca padrão)."""

    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str = cfg.LLM_MODEL, api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("Defina ANTHROPIC_API_KEY para usar LLM_PROVIDER=anthropic")
        self.name = f"anthropic:{model}"

    def complete(self, system: str, messages: list[dict]) -> str:
        body = json.dumps({
            "model": self.model, "max_tokens": 900, "temperature": 0,
            "system": system, "messages": messages,
        }).encode("utf-8")
        req = urllib.request.Request(self.URL, data=body, method="POST", headers={
            "content-type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise _http_error(exc) from None
        return "".join(b.get("text", "") for b in data.get("content", []))


class GeminiLLM:
    """Cliente da API Gemini. O plano gratuito limita requisições por minuto: espaça e repete em 429."""

    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    RETRY_STATUS = {429, 500, 503}

    def __init__(self, model: str | None = None, api_key: str | None = None,
                 delay_s: float | None = None, max_retries: int = 3):
        raw = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        # aceita "models/gemini-..." (como aparece nas mensagens do Google), espaços e aspas
        self.model = raw.strip().strip("'\"").removeprefix("models/")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Defina GEMINI_API_KEY para usar LLM_PROVIDER=gemini")
        self.delay_s = float(os.getenv("GEMINI_DELAY_S", "4")) if delay_s is None else delay_s
        self.max_retries = max_retries
        self.name = f"gemini:{self.model}"
        self._last_call = 0.0

    def _body(self, system: str, messages: list[dict]) -> bytes:
        contents = [
            {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
            for m in messages
        ]
        return json.dumps({
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }).encode("utf-8")

    def complete(self, system: str, messages: list[dict]) -> str:
        body = self._body(system, messages)
        url = self.URL.format(model=self.model)
        for attempt in range(self.max_retries + 1):
            wait = self.delay_s - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, data=body, method="POST", headers={
                "content-type": "application/json",
                "x-goog-api-key": self.api_key,
            })
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self._last_call = time.monotonic()
                break
            except urllib.error.HTTPError as exc:
                self._last_call = time.monotonic()
                if exc.code in self.RETRY_STATUS and attempt < self.max_retries:
                    time.sleep(min(2 ** attempt * 5, 30))
                    continue
                err = _http_error(exc)
                if exc.code == 404:
                    err = RuntimeError(f"{err} | Dica: o modelo '{self.model}' pode ter sido descontinuado; "
                                       "troque com a variável GEMINI_MODEL (veja os modelos em aistudio.google.com)")
                raise err from None
        parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts if not p.get("thought"))

    def listar_modelos(self) -> list[str]:
        """Nomes de modelos que aceitam generateContent com a sua chave."""
        url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=200"
        req = urllib.request.Request(url, headers={"x-goog-api-key": self.api_key, "User-Agent": "citizentech/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise _http_error(exc) from None
        return sorted(m["name"].removeprefix("models/") for m in data.get("models", [])
                      if "generateContent" in m.get("supportedGenerationMethods", []))


class OpenAICompatLLM:
    """Formato OpenAI (/chat/completions): serve para Groq, OpenRouter, Mistral e Ollama local."""

    RETRY_STATUS = {429, 500, 502, 503}

    def __init__(self, base_url: str, api_key: str, model: str, label: str = "openai_compat",
                 delay_s: float | None = None, max_retries: int = 3):
        if not base_url or not api_key or not model:
            raise RuntimeError(f"{label}: defina URL base, chave e modelo (veja o README)")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model.strip().strip("'\"")
        self.delay_s = float(os.getenv("LLM_DELAY_S", "2")) if delay_s is None else delay_s
        self.max_retries = max_retries
        self.name = f"{label}:{self.model}"
        self._last_call = 0.0

    def _headers(self) -> dict:
        # User-Agent próprio: alguns provedores (atrás de Cloudflare) bloqueiam o padrão do urllib
        return {"content-type": "application/json", "authorization": f"Bearer {self.api_key}",
                "user-agent": "citizentech/1.0"}

    def complete(self, system: str, messages: list[dict]) -> str:
        body = json.dumps({
            # Teto alto porque modelos de raciocínio (gpt-oss, o-series) gastam tokens pensando antes
            # de escrever: com 900 o JSON era cortado no meio e a resposta voltava vazia.
            "model": self.model, "temperature": 0,
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2500")),
            "messages": [{"role": "system", "content": system}] + messages,
        }).encode("utf-8")
        for attempt in range(self.max_retries + 1):
            wait = self.delay_s - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(self.base_url + "/chat/completions", data=body, method="POST",
                                         headers=self._headers())
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self._last_call = time.monotonic()
                break
            except urllib.error.HTTPError as exc:
                self._last_call = time.monotonic()
                if exc.code in self.RETRY_STATUS and attempt < self.max_retries:
                    time.sleep(min(2 ** attempt * 5, 30))
                    continue
                err = _http_error(exc)
                if exc.code in (400, 404):
                    err = RuntimeError(f"{err} | Dica: confira o nome do modelo; liste os disponíveis com "
                                       "python -m ia.smoke --modelos")
                raise err from None
        choices = data.get("choices") or [{}]
        return (choices[0].get("message") or {}).get("content") or ""

    def listar_modelos(self) -> list[str]:
        req = urllib.request.Request(self.base_url + "/models", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise _http_error(exc) from None
        return sorted(m["id"] for m in data.get("data", []))


def get_llm(provider: str | None = None):
    provider = (provider or cfg.LLM_PROVIDER).lower()
    if provider == "mock":
        return MockLLM()
    if provider == "anthropic":
        return AnthropicLLM()
    if provider == "gemini":
        return GeminiLLM()
    if provider == "groq":
        return OpenAICompatLLM("https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY", ""),
                               os.getenv("GROQ_MODEL", ""), label="groq")
    if provider == "openai_compat":
        return OpenAICompatLLM(os.getenv("LLM_BASE_URL", ""), os.getenv("LLM_API_KEY", ""),
                               os.getenv("LLM_MODEL", ""), label="openai_compat")
    raise ValueError(f"LLM_PROVIDER desconhecido: {provider!r} (use mock, gemini, groq, openai_compat ou anthropic)")
