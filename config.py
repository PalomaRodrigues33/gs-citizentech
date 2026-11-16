"""Configuração central do CitizenTech (assistente do cidadão para o SP156)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
DB_PATH = DATA_DIR / "citizentech.db"
MODEL_PATH = DATA_DIR / "modelo_7dias.pkl"
WEB_DIST = BASE_DIR / "web" / "dist"

SP156_FILE = os.getenv("SP156_FILE", "")   # vazio = procura em data/raw/

# Pelo INÍCIO do nome do serviço, não por palavra solta: "calçadas" também aparece em poda de árvore.
GRUPOS = {
    "Buraco": ("tapa-buraco",),
    "Calçada e acessibilidade": (
        "calçada pública", "calçada particular", "acessibilidade - solicitar avaliação de obstáculo",
        "sugerir construção de calçadas", "guia rebaixada", "guias para travessia"),
    "Entulho e lixo": (
        "entulho e grandes objetos", "denunciar descarte irregular de entulho", "denunciar caçamba irregular"),
    "Varrição": ("fazer reclamação de falta de varrição", "sacos de varrição"),
    "Bueiro": ("solicitar limpeza de bueiros",),
}

# Os 13 serviços exatos do recorte. A IA tem que escolher um destes.
SERVICOS = {
    "Tapa-buraco": "Buraco",
    "Tapa-buraco em faixa exclusiva ou corredor de ônibus": "Buraco",
    "Calçada pública - solicitar manutenção": "Calçada e acessibilidade",
    "Calçada particular - denunciar calçada danificada ou inexistente": "Calçada e acessibilidade",
    "Acessibilidade - solicitar avaliação de obstáculo na calçada": "Calçada e acessibilidade",
    "Guias para travessia de pedestres - Solicitar rebaixamento": "Calçada e acessibilidade",
    "Guia rebaixada - solicitar fiscalização de rebaixamento irregular": "Calçada e acessibilidade",
    "Sugerir construção de calçadas em áreas públicas e praças": "Calçada e acessibilidade",
    "Entulho e grandes objetos em via pública - solicitar remoção": "Entulho e lixo",
    "Denunciar descarte irregular de entulho e outros resíduos em área pública": "Entulho e lixo",
    "Denunciar caçamba irregular de entulho de construção": "Entulho e lixo",
    "Fazer reclamação de falta de varrição": "Varrição",
    "Sacos de varrição - Fazer reclamação de falta de remoção": "Varrição",
    "Solicitar limpeza de bueiros, boca de lobo e poços de visita": "Bueiro",
}

# A coluna do SP156 é "Prefeitura Operacional": quase sempre é a subprefeitura da região, mas às vezes
# é o órgão que executou o serviço. Órgão não é bairro de ninguém, então fica fora da lista de regiões.
ORGAOS_NAO_REGIAO = (
    "Superintendencia das Usinas de Asfalto",
    "Departamento de Estradas de Rodagem",
    "Secretaria Municipal do Verde e do Meio Ambiente",
)

# Página de cada serviço no portal, para o link cair no lugar certo em vez da home.
# Os ids foram conferidos um por um em 16/11/2026: a página /portal/servicos/informacao?servico=<id>
# responde 200 e o título bate com o nome do serviço. Quem não está aqui cai no portal geral.
SERVICOS_PORTAL = {
    "Tapa-buraco": 952,
    "Tapa-buraco em faixa exclusiva ou corredor de ônibus": 3170,
    "Calçada pública - solicitar manutenção": 931,
    "Calçada particular - denunciar calçada danificada ou inexistente": 906,
    "Guias para travessia de pedestres - Solicitar rebaixamento": 766,
    "Guia rebaixada - solicitar fiscalização de rebaixamento irregular": 919,
    "Entulho e grandes objetos em via pública - solicitar remoção": 2641,
    "Denunciar descarte irregular de entulho e outros resíduos em área pública": 915,
    "Denunciar caçamba irregular de entulho de construção": 751,
    "Fazer reclamação de falta de varrição": 945,
    "Sacos de varrição - Fazer reclamação de falta de remoção": 946,
}
PORTAL_SERVICO_URL = "https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico={id}"


def url_do_servico(nome: str):
    """Link da página oficial do serviço. Sai daqui, nunca do modelo."""
    sid = SERVICOS_PORTAL.get(nome)
    return PORTAL_SERVICO_URL.format(id=sid) if sid else None


# Canais oficiais, conferidos em 14/11/2026. Saem daqui, nunca do modelo: ele não pode inventar link.
CANAIS = [
    {"id": "portal", "nome": "Portal SP156", "como": "sp156.prefeitura.sp.gov.br, pelo navegador",
     "url": "https://sp156.prefeitura.sp.gov.br/portal",
     "fonte": "https://prefeitura.sp.gov.br/web/subprefeituras/w/calcadas/37497"},
    {"id": "app", "nome": "Aplicativo SP156", "como": "Procure \"SP156\" na loja do Android ou do iPhone",
     "url": None, "fonte": "https://prefeitura.sp.gov.br/web/subprefeituras/w/calcadas/37497"},
    {"id": "whatsapp", "nome": "WhatsApp (Chat SP156)", "como": "(11) 3230-5156",
     "url": "https://wa.me/551132305156",
     "fonte": "https://prefeitura.sp.gov.br/noticia/prefeitura-lanca-servico-do-156-pelo-whatsapp-para-agilizar-atendimento-a-populacao"},
    {"id": "telefone", "nome": "Central 156", "como": "Ligue 156", "url": "tel:156",
     "fonte": "https://prefeitura.sp.gov.br/web/subprefeituras/w/calcadas/37497"},
]
CHECKLIST = ["Endereço completo", "Ponto de referência", "Desde quando o problema existe", "Foto nítida do local"]
EMERGENCIA = "Risco imediato à vida (fio caído, desabamento, alagamento com pessoas em perigo): ligue 193 (Bombeiros) ou 199 (Defesa Civil)."

DATA_CORTE = "2026-09-30"
JANELA_RESOLUCAO_DIAS = 7
SEED = 42

SP_BBOX = {"lat_min": -24.1, "lat_max": -23.2, "lon_min": -47.0, "lon_max": -46.3}
LOCAL_DECIMALS = 4            # 4 casas = ~11 m: é o que conta como "mesmo local"

TREINO_CORTE = "2026-08-31"   # corte temporal: treina até aqui, testa em setembro
MIN_PEDIDOS_DISTRITO = 30     # abaixo disso o contexto usa a subprefeitura inteira
TENDENCIA_INICIO = "2026-07-13"   # 01-12/07 teve quebra na série em todos os tipos: fica fora da tendência

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")   # mock | groq | gemini | openai_compat | anthropic
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5")
TEXTO_MIN, TEXTO_MAX = 10, 500
LOG_EXEMPLOS = os.getenv("LOG_EXEMPLOS", "1") == "1"

LIMITE_ASSISTENTE_POR_MIN = int(os.getenv("LIMITE_ASSISTENTE_POR_MIN", "10"))   # por IP
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o]
