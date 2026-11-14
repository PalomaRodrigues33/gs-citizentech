# CitizenTech: a zeladoria do seu bairro, com dados do SP156

> **Vídeo pitch:** _(inserir link público aqui)_ · **Integrantes:** ver `grupo.txt`

**Para quem:** moradores de São Paulo, em especial idosos, pessoas com deficiência e quem anda com carrinho de
bebê, que dependem de ruas e calçadas em bom estado.

**Problema:** o morador não sabe quanto tempo a Prefeitura leva para resolver um buraco ou uma calçada quebrada
no bairro dele, não sabe em qual dos serviços do SP156 abrir o pedido, e não vê onde os problemas estão parados
há meses.

**O que o app faz** (sem substituir o SP156: quem recebe e resolve é a Prefeitura):

| Tela | Pergunta que responde |
|---|---|
| **Meu bairro** | Quanto tempo cada tipo de problema leva aqui? A região está melhorando? Como se compara às outras? |
| **Fazer pedido** | Em qual serviço do SP156 abro isto, o que escrevo e o que mais preciso informar? (IA) |
| **Atrasos** | Onde a Prefeitura está mais atrasada perto de mim? (transparência pública) |
| **Como funciona** | De onde vêm os dados, o que a IA faz e o que os números não dizem |

O app é feito para celular (React) e conversa com uma API em Python que guarda os dados, o modelo e a IA.
Ele **não recebe nem guarda pedidos**: prepara o texto e leva o cidadão ao canal oficial (portal, aplicativo,
WhatsApp ou telefone 156).

## Como executar

### 1. Baixe os dados do SP156 (uma vez)

No [Portal de Dados Abertos](https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156), baixe o arquivo de
solicitações do 3º trimestre de 2026 (`arquivo-final-3-trim-26.xlsx`) e salve em `data/raw/`.

A pasta `data/` não vem no repositório (é gerada). Se ela não existir, `python run_all.py` cria `data/raw/` e
mostra o caminho exato onde colocar o arquivo.

### 2a. Sem Docker (Python 3.12+ e Node 20+), Windows PowerShell

```powershell
python -m pip install -r requirements.txt
python run_all.py                          # 5 etapas: ingestão, limpeza, IA, atrasos, análises

cd web; npm install; npm run build; cd ..
python -m uvicorn api.main:app --port 8000 # app em http://localhost:8000 · API em /docs

python -m pytest -v                        # 37 testes
```

Use `python -m pip` e `python -m uvicorn`: no Windows, `pip` e `uvicorn` sozinhos muitas vezes não estão no PATH.
(No Linux/macOS os mesmos comandos funcionam; troque `;` por `&&` se preferir.)

### 2b. Com Docker

```powershell
docker compose run --rm pipeline       # gera as camadas, o modelo e o banco (~1 min)
docker compose up --build app          # app e API em http://localhost:8000
docker compose --profile test run --rm tests
```

A imagem é construída e testada automaticamente a cada push (ver [Integração contínua](#integração-contínua)).

**No celular:** com o computador e o celular na mesma rede Wi-Fi, rode a API com `--host 0.0.0.0` e abra
`http://IP-DO-COMPUTADOR:8000` no navegador do celular. Pelo menu do navegador, "Adicionar à tela inicial"
instala o app como um ícone.

**Para mexer no app** (recarrega a cada alteração): deixe a API rodando e, em outro terminal,
`cd web; npm run dev` → http://localhost:5173.

## Dados

**SP156 – Solicitações** (Prefeitura de São Paulo, dados abertos), de 01/07 a 30/09/2026: 484.232 pedidos, dos
quais 84.487 são de zeladoria de ruas e calçadas em 13 serviços (buraco, calçada e acessibilidade, entulho,
varrição e bueiro). O arquivo não tem dados pessoais de quem pediu. **Nenhum dado é simulado.**

Achados que o app mostra (dados reais):

- 9 em cada 10 pedidos de **obstáculo na calçada** (acessibilidade) e de **calçada particular danificada**
  seguiam abertos em 30/09. Entulho e varrição são resolvidos em 1 dia na maioria dos casos.
- 17% dos pontos com pedido têm mais de um pedido no mesmo lugar: muita gente reclama da mesma coisa.

Detalhes, recorte e decisões de tratamento em [`docs/fontes_de_dados.md`](docs/fontes_de_dados.md).

## Arquitetura

```
data/raw     arquivo original do SP156, intocado               (fora do Git)
   ↓ ingestion/sp156.py      recorta os 13 serviços de zeladoria
data/bronze  recorte bruto, como veio
   ↓ pipeline/silver.py      tipos, validações, dias até resolver, alvo de 7 dias, local do problema
data/silver  limpo + tabela `pedidos` no SQLite
   ↓ ml/modelo.py            IA 1: chance de resolução em 7 dias
   ↓ transparencia/          lista de atrasos (rua + tipo, dias de espera somados)
   ↓ analytics/sql/          4 consultas com funções de janela
data/gold    lista de atrasos, análises, métricas + tabelas no SQLite
   ↓ api/ (FastAPI)          regiões, indicadores, atrasos, IA 2 (assistente de pedido)
web/ (React)                 app para celular, servido pela própria API
```

Diagrama e decisões em [`docs/arquitetura.md`](docs/arquitetura.md).

## Funções analíticas (SQL com funções de janela)

Cada consulta em `analytics/sql/` responde a uma pergunta do cidadão e alimenta um gráfico do app:

| Consulta | Pergunta | Funções de janela |
|---|---|---|
| `tempo_por_tipo` | Quanto tempo cada tipo leva aqui? | `ROW_NUMBER()`, `COUNT() OVER (PARTITION BY)` (mediana) |
| `tendencia_semanal` | A região está melhorando? | `AVG() OVER (ROWS BETWEEN 2 PRECEDING ...)`, `LAG()` |
| `ranking_regioes` | Como se compara às outras? | `RANK()`, `NTILE(3)`, `COUNT() OVER ()`, `SUM() OVER ()` |
| `atrasos` | Onde está mais atrasado? | `ROW_NUMBER()`, `PERCENT_RANK()` |

Todas recebem os filtros do app (região e tipo de problema) como **parâmetros**, nunca como texto concatenado.

## IA

Duas IAs, cada uma com o ganho medido contra o que existiria sem ela ([`docs/ia.md`](docs/ia.md)):

1. **Previsão de resolução em 7 dias** (gradient boosting, dados reais). Treina em julho e agosto, é testada em
   setembro. AUC 0,861 contra 0,830 da regra simples; **dentro de cada tipo de problema** a regra simples não
   distingue nada (AUC 0,50) e o modelo chega a 0,90 em calçadas.
2. **Assistente de pedido** (LLM com prompt de papel, regras e exemplos; saída JSON validada). Lê o relato livre,
   escolhe o **serviço exato** entre os 13 do SP156, escreve o texto do pedido e lista o que falta informar.
   Sem chave de API, roda com regras de palavras-chave (`LLM_PROVIDER=mock`, 83% de acerto no serviço em 30
   relatos rotulados). **É esse modo que foi avaliado e aparece na demonstração**; o número é otimista porque as
   regras foram escritas olhando os mesmos relatos. A integração com LLM está pronta, mas não foi medida com um
   LLM real nesta entrega. Para medir:

```powershell
$env:LLM_PROVIDER="groq"; $env:GROQ_API_KEY="sua-chave"
python -m ia.smoke --modelos        # lista os modelos da sua chave
$env:GROQ_MODEL="modelo-da-lista"
python -m ia.avaliacao              # antes x depois -> data/gold/metricas_assistente.json
```

Nunca versione a chave. Se o LLM falhar, o app entrega um rascunho simples e avisa; nada se perde.

## Segurança e privacidade

- **Nenhum dado pessoal:** o app não pede nome, e-mail, telefone nem documento, e não guarda os pedidos.
- **Entradas validadas** (Pydantic + regiões e tipos que existem nos dados); **SQL sempre parametrizado**.
- **Proteção contra injeção no prompt:** o relato vai num bloco marcado que o usuário não consegue fechar; a saída
  só aceita serviços da lista; links e telefones vêm do código, nunca do modelo (teste CT-23 remove um link de golpe).
- **Limite de chamadas** ao assistente por IP (protege a cota do LLM).
- **Cabeçalhos de segurança** e Content-Security-Policy restritiva; chaves só por variável de ambiente.

## Integração contínua

A cada push no GitHub, o workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda três etapas:

| Job | O que faz |
|---|---|
| `testes` | Instala as dependências Python e roda `pytest` |
| `web` | Instala e compila o app React |
| `docker` | Constrói a imagem do `Dockerfile`, roda os testes dentro do contêiner e sobe a API, conferindo `/api/saude` |

No CI não há o arquivo do SP156 (29 MB, fora do Git), então os testes que precisam dos dados gerados são
pulados e aparecem como `SKIPPED` no log. Os demais rodam normalmente.

## Limitações

- "Finalizado" no SP156 significa pedido encerrado, **não necessariamente problema consertado**.
- A chance de solução é estatística, não um prazo da Prefeitura.
- Os dados vão até 30/09/2026; o app não acompanha protocolos em tempo real (não há API pública para isso).
- Nas duas primeiras semanas de julho os prazos subiram em todos os tipos e na cidade inteira ao mesmo tempo
  (provável mudança operacional ou de registro); a tendência começa em 13/07.

## Estrutura

```
ingestion/      leitura do SP156 e recorte (bronze)
pipeline/       silver (limpeza e derivadas) e gold
analytics/sql/  consultas com funções de janela
ml/             modelo de chance de resolução em 7 dias
transparencia/  lista pública de atrasos
ia/             assistente: prompt, provedores de LLM, avaliação, teste rápido
api/            FastAPI: rotas, validação, segurança
web/            app React para celular
tests/          37 testes (docs/plano_de_testes.md)
docs/           arquitetura, fontes de dados, IA, plano de testes
```
