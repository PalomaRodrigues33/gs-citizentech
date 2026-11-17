"""Configuração do pytest: põe a raiz do projeto no caminho de importação."""
import config as cfg

cfg.LOG_EXEMPLOS = False

# Testes rodam sempre no assistente de regras, mesmo com um .env configurado na máquina. Sem isso a suíte
# chamava a API do provedor de verdade: ficava lenta, gastava cota e falhava com 429 por motivo nenhum.
# Quem quiser medir o modelo real usa `python -m ia.avaliacao`, que é o lugar certo para isso.
cfg.LLM_PROVIDER = "mock"
