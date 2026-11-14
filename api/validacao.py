"""Validação das entradas da API (o cidadão nunca informa nome, e-mail, telefone ou documento)."""
from pydantic import BaseModel, Field, field_validator

import config as cfg


class PedidoAssistente(BaseModel):
    texto: str = Field(..., description="Relato livre do problema")
    subprefeitura: str
    distrito: str

    @field_validator("texto")
    @classmethod
    def _texto(cls, v: str) -> str:
        t = " ".join((v or "").split())
        if len(t) < cfg.TEXTO_MIN:
            raise ValueError(f"Descreva o problema com pelo menos {cfg.TEXTO_MIN} caracteres.")
        if len(t) > cfg.TEXTO_MAX:
            raise ValueError(f"O relato deve ter no máximo {cfg.TEXTO_MAX} caracteres.")
        return t


def validate_region(subprefeitura: str | None, distrito: str | None, regioes: dict) -> str | None:
    """Mensagem de erro, ou None se a região existe nos dados reais."""
    if subprefeitura is not None and subprefeitura not in regioes:
        return "Subprefeitura desconhecida."
    if distrito is not None and (subprefeitura is None or distrito not in regioes[subprefeitura]):
        return "Distrito não pertence à subprefeitura escolhida."
    return None


def validate_group(grupo: str | None) -> str | None:
    if grupo is not None and grupo not in cfg.GRUPOS:
        return "Tipo de problema desconhecido."
    return None
