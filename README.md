# ZeladoriaSP — zeladoria do seu bairro, com dados do SP156

> **Vídeo pitch:** _https://www.youtube.com/watch?v=9661oN_Dv1M_ ·

O ZeladoriaSP mostra quanto tempo a Prefeitura de São Paulo leva para resolver problemas de rua e calçada no bairro do cidadão — buraco no asfalto, calçada quebrada, falta de acessibilidade, entulho e descarte irregular de lixo, entre outros, e prepara o pedido certo no SP156. Pensado para quem depende de ruas e calçadas em bom estado — em especial idosos, pessoas com deficiência e quem anda com carrinho de bebê.

Ele **não recebe nem guarda pedidos**: só prepara o texto e leva o cidadão ao canal oficial (portal, aplicativo,
WhatsApp ou telefone 156). Quem recebe e resolve é a Prefeitura.

| Tela | Pergunta que responde |
|---|---|
| **Meu bairro** | Quanto tempo cada tipo de problema leva aqui? A região está melhorando? Como se compara às outras? |
| **Fazer pedido** | Em qual serviço do SP156 abro isto, o que escrevo e o que falta informar? (IA) |
| **Atrasos** | Onde a Prefeitura está mais atrasada perto de mim? (transparência pública) |
| **Como funciona** | De onde vêm os dados, o que a IA faz e o que os números não dizem |

## Como executar

Pré-requisitos: **Python 3.12+**, **Node 20+** e **Git**. O arquivo de dados do SP156 já vem no repositório.

```powershell
git clone https://github.com/PalomaRodrigues33/gs-citizentech
cd gs-citizentech
python iniciar.py
```

Depois abra **http://localhost:8000**. O `iniciar.py` faz tudo: instala as dependências que faltam, gera os
dados e o modelo, compila o app React e sobe o servidor. A primeira vez leva uns 3 minutos; nas seguintes,
segundos.

### Ligar o modelo de linguagem (opcional)

Sem essa etapa o app já funciona por completo, com o assistente escolhendo o serviço por **regras de
palavra-chave** (83,3% de acerto). Para usar o modelo de linguagem (93,3% de acerto, tabela abaixo):

1. Crie uma chave gratuita em [console.groq.com/keys](https://console.groq.com/keys).
2. Copie `.env.exemplo` para `.env` e cole a chave em `GROQ_API_KEY`.
3. Rode `python iniciar.py` de novo. A tela "Como funciona" deixa de avisar que está sem chave.

O `.env` está no `.gitignore` e nunca é versionado. Se a Groq tiver aposentado o modelo do exemplo, veja os
nomes atuais com `python -m ia.smoke --modelos` e ajuste `GROQ_MODEL`. Para refazer a medição de antes e
depois: `python -m ia.avaliacao`.

<details>
<summary>Outras opções: celular, testes, Docker, etapa por etapa</summary>

```powershell
python iniciar.py --rede          # abrir no celular, pela mesma rede Wi-Fi
python iniciar.py --porta 8001    # se a porta 8000 estiver ocupada
python -m pytest -v               # 41 testes
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
pediu. **Nenhum dado é simulado.** O recorte, as decisões de tratamento e as fontes oficiais estão no PDF do projeto.

Dois achados do app: 9 em cada 10 pedidos de **obstáculo na calçada** e de **calçada particular danificada**
seguiam abertos em 30/09, enquanto entulho e varrição saem em 1 dia na maioria dos casos; e 17% dos pontos têm
mais de um pedido no mesmo lugar.

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

Diagrama em [`capturas/arquitetura.png`](capturas/arquitetura.png) (fonte Mermaid em `capturas/arquitetura.mmd`).

## O que tem dentro

| Área | O que foi feito | Detalhe |
|---|---|---|
| **Funções analíticas** | 4 consultas SQL com funções de janela (`ROW_NUMBER`, `LAG`, `RANK`, `NTILE`, `PERCENT_RANK`, média móvel), sempre parametrizadas | `analytics/sql/` |
| **IA 1 — previsão** | Chance de resolução em 7 dias. Treina em jul–ago, testa em setembro: AUC **0,861** contra 0,830 da regra simples; dentro de cada tipo a regra não distingue nada (0,50) e o modelo chega a 0,90 | `ml/modelo.py` |
| **IA 2 — assistente** | Lê o relato livre e escolhe o **serviço exato** entre os 13, escreve o pedido e lista o que falta. Com o modelo de linguagem acerta o serviço exato em **93,3%** dos 30 relatos rotulados, contra 83,3% das regras de palavra-chave (o grupo do problema vai a 100%). Sem chave de API continua funcionando pelas regras | `ia/assistente.py` |
| **Segurança** | Nenhum dado pessoal pedido ou guardado; entradas validadas; SQL parametrizado; proteção contra injeção de prompt; limite de chamadas por IP; CSP restritiva; chave de API só em variável de ambiente | `api/`, `tests/` |
| **Qualidade** | 41 testes automatizados | `tests/` |
| **CI** | A cada push, o GitHub Actions gera os dados e roda os **41 testes**, compila o app e **constrói a imagem Docker**, repetindo o pipeline e os testes dentro do contêiner antes de subir a API e conferir `/api/saude` | [`ci.yml`](.github/workflows/ci.yml) |

A documentação completa — arquitetura, indicadores, prompt da IA, plano de testes e evidências de
execução — está no **PDF entregue junto com este repositório**.

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
tests/                                                   41 testes automatizados
capturas/                                                diagrama da arquitetura e telas do app
```
