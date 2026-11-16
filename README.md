# CitizenTech: a zeladoria do seu bairro, com dados do SP156

> **Vídeo pitch:** _(inserir link público aqui)_ · **Integrantes:** ver `grupo.txt`

App de celular que mostra quanto tempo a Prefeitura de São Paulo leva para resolver buracos e calçadas no seu
bairro, e ajuda a abrir o pedido certo no SP156. Feito para quem depende de ruas e calçadas em bom estado: em
especial idosos, pessoas com deficiência e quem anda com carrinho de bebê.

Ele **não recebe nem guarda pedidos**. Prepara o texto e leva o cidadão ao canal oficial (portal, aplicativo,
WhatsApp ou telefone 156); quem recebe e resolve é a Prefeitura.

| Tela | Pergunta que responde |
|---|---|
| **Meu bairro** | Quanto tempo cada tipo de problema leva aqui? A região está melhorando? Como se compara às outras? |
| **Fazer pedido** | Em qual serviço do SP156 abro isto, o que escrevo e o que falta informar? (IA) |
| **Atrasos** | Onde a Prefeitura está mais atrasada perto de mim? (transparência pública) |
| **Como funciona** | De onde vêm os dados, o que a IA faz e o que os números não dizem |

## Como executar

Precisa de **Python 3.12+** e **Node 20+**. O arquivo de dados do SP156 já vem no repositório.

```powershell
python iniciar.py
```

Depois abra **http://localhost:8000**. Esse comando faz tudo: instala as dependências que faltam, gera os dados
e o modelo, compila o app React e sobe o servidor. A primeira vez leva uns 3 minutos; nas seguintes, segundos.

<details>
<summary>Outras opções: celular, testes, Docker, etapa por etapa</summary>

```powershell
python iniciar.py --rede          # abrir no celular, pela mesma rede Wi-Fi
python iniciar.py --porta 8001    # se a porta 8000 estiver ocupada
python -m pytest -v               # 38 testes
```

As mesmas etapas na mão, sem o `iniciar.py`:

```powershell
python -m pip install -r requirements.txt
python run_all.py                          # 5 etapas: ingestão, limpeza, IA, atrasos, análises
cd web; npm install; npm run build; cd ..
python -m uvicorn api.main:app --port 8000
```

No Windows, use `python -m pip` e `python -m uvicorn`: sozinhos, `pip` e `uvicorn` muitas vezes não estão no
PATH. No Linux e no macOS os mesmos comandos funcionam.

Com Docker:

```powershell
docker compose run --rm pipeline
docker compose up --build app
docker compose --profile test run --rm tests
```

Para mexer no app, com recarga a cada alteração: deixe a API rodando e, em outro terminal, `cd web; npm run dev`.

</details>

## Dados

**SP156 – Solicitações** (Prefeitura de São Paulo, dados abertos), de 01/07 a 30/09/2026: 484.232 pedidos, dos
quais **84.487** são de zeladoria de ruas e calçadas, em 13 serviços. O arquivo não tem dado pessoal de quem
pediu. **Nenhum dado é simulado.** Recorte e decisões em [`docs/fontes_de_dados.md`](docs/fontes_de_dados.md).

Dois achados que o app mostra: 9 em cada 10 pedidos de **obstáculo na calçada** e de **calçada particular
danificada** seguiam abertos em 30/09, enquanto entulho e varrição saem em 1 dia na maioria dos casos; e 17% dos
pontos têm mais de um pedido no mesmo lugar.

## Arquitetura

```
data/raw     arquivo original do SP156, intocado
   ↓ ingestion/sp156.py      recorta os 13 serviços de zeladoria
data/bronze  recorte bruto, como veio
   ↓ pipeline/silver.py      tipos, validações, dias até resolver, alvo de 7 dias, local do problema
data/silver  limpo + tabela `pedidos` no SQLite
   ↓ ml/modelo.py            IA 1: chance de resolução em 7 dias
   ↓ transparencia/          lista de atrasos (rua + tipo, dias de espera somados)
   ↓ analytics/sql/          4 consultas com funções de janela
data/gold    lista de atrasos, análises e métricas + tabelas no SQLite
   ↓ api/ (FastAPI)          regiões, indicadores, atrasos, IA 2 (assistente de pedido)
web/ (React)                 app para celular, servido pela própria API
```

Diagrama e decisões em [`docs/arquitetura.md`](docs/arquitetura.md).

## O que tem dentro

| Área | O que foi feito | Detalhe |
|---|---|---|
| **Funções analíticas** | 4 consultas SQL com funções de janela (`ROW_NUMBER`, `LAG`, `RANK`, `NTILE`, `PERCENT_RANK`, média móvel), sempre parametrizadas | `analytics/sql/` |
| **IA 1 — previsão** | Chance de resolução em 7 dias. Treina em jul–ago, testa em setembro: AUC **0,861** contra 0,830 da regra simples; dentro de cada tipo a regra não distingue nada (0,50) e o modelo chega a 0,90 | [`docs/ia.md`](docs/ia.md) |
| **IA 2 — assistente** | Lê o relato livre e escolhe o **serviço exato** entre os 13, escreve o pedido e lista o que falta. Sem chave de API roda por regras (83% de acerto, número otimista); a integração com LLM está pronta, mas não foi medida nesta entrega | [`docs/ia.md`](docs/ia.md) |
| **Segurança** | Nenhum dado pessoal pedido ou guardado; entradas validadas; SQL parametrizado; proteção contra injeção de prompt; limite de chamadas por IP; CSP restritiva | [`docs/plano_de_testes.md`](docs/plano_de_testes.md) |
| **Qualidade** | 38 testes automatizados | `tests/` |
| **CI** | A cada push, o GitHub Actions gera os dados e roda os **38 testes**, compila o app e **constrói a imagem Docker**, repetindo o pipeline e os testes dentro do contêiner antes de subir a API e conferir `/api/saude` | [`ci.yml`](.github/workflows/ci.yml) |

## Limitações

- "Finalizado" no SP156 significa pedido encerrado, **não necessariamente problema consertado**.
- A chance de solução é estatística, não um prazo da Prefeitura.
- Os dados vão até 30/09/2026; o app não acompanha protocolos em tempo real (não há API pública para isso).
- Nas duas primeiras semanas de julho os prazos subiram em todos os tipos e na cidade inteira ao mesmo tempo
  (provável mudança operacional ou de registro); por isso a tendência começa em 13/07.

## Estrutura

```
ingestion/  pipeline/  analytics/  ml/  transparencia/   camadas de dados e análise
ia/                                                      assistente: prompt, LLM, avaliação
api/                                                     FastAPI: rotas, validação, segurança
web/                                                     app React para celular
tests/  docs/                                            38 testes e documentação
```
