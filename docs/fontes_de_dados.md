# Fontes de dados

## SP156 – Solicitações (dado real, único dado usado)

- **Origem:** Prefeitura de São Paulo, [Portal de Dados Abertos](https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156),
  arquivo do 3º trimestre de 2026.
- **Volume:** 484.232 pedidos e 15 colunas; abertura de 01/07 a 30/09/2026, finalizações até 08/10/2026.
- **Privacidade:** sem dados pessoais de quem pediu (só serviço, status, datas e endereço do problema).
- **Colunas usadas:** Data de Abertura, Data de Finalização, Serviço, Status, Logradouro, Latitude, Longitude,
  Prefeitura Operacional (subprefeitura) e Distrito.

### Recorte: 13 serviços de zeladoria de ruas e calçadas (84.487 pedidos)

A classificação usa o **início do nome do serviço**, não palavras soltas: "calçada" aparece também em pedidos de
poda de árvore e de fiação, que não são problemas de calçada (teste CT-02).

| Serviço | Pedidos | Resolvidos em até 7 dias | Ainda abertos em 30/09 |
|---|---:|---:|---:|
| Entulho e grandes objetos em via pública | 32.795 | 89% | 1% |
| Tapa-buraco | 29.024 | 47% | 28% |
| Falta de varrição | 9.349 | 92% | 1% |
| Limpeza de bueiros e bocas de lobo | 5.757 | 75% | 9% |
| Calçada pública – manutenção | 1.461 | 36% | 41% |
| Descarte irregular de entulho (denúncia) | 1.376 | 52% | 50% |
| Acessibilidade – obstáculo na calçada | 1.192 | **3%** | **90%** |
| Sacos de varrição não removidos | 1.023 | 92% | 1% |
| Tapa-buraco em corredor de ônibus | 938 | 33% | 35% |
| Calçada particular danificada (denúncia) | 835 | **1%** | **91%** |
| Guia rebaixada irregular (fiscalização) | 277 | 0% | 97% |
| Rebaixamento de guia para travessia | 223 | 52% | 22% |
| Construção de calçada em área pública (sugestão) | 143 | 97% | 3% |
| Caçamba irregular (denúncia) | 94 | 8% | 29% |

Os serviços que mais afetam idosos, pessoas com deficiência e carrinhos de bebê — obstáculo na calçada e
calçada danificada — são os que quase nunca são encerrados no trimestre.

## Decisões de tratamento

- **Só há data, sem hora:** prazos em dias inteiros.
- **Resultado desconhecido não vira "não resolvido".** O alvo `resolvido_7d` só existe para aberturas até 23/09
  (a janela de 7 dias já fechou) e para pedidos não cancelados: 76.359 pedidos com alvo, 8.128 sem.
- **"Finalizado" não é "consertado".** O SP156 registra o encerramento do pedido. A taxa de 97% em "sugestão de
  construção de calçada" mostra isso: o pedido é respondido, não a calçada construída. O app diz isso na tela
  "Como funciona".
- **Quebra na série no início de julho.** De 01 a 12/07, os prazos subiram ao mesmo tempo em todos os tipos e na
  cidade inteira (entulho: 24% resolvidos em 7 dias, contra 99% a partir de 13/07; varrição: 29% contra 98% a 100%).
  Uma mudança dessas, simultânea em toda a cidade, indica alteração na operação ou no registro, não nos bairros.
  Por isso a tendência semanal começa em 13/07. O número principal de cada região usa o trimestre inteiro.
- **Qualidade:** no recorte, 5 pedidos sem coordenada e 2 fora da região de São Paulo (coordenadas anuladas,
  pedido mantido); nenhuma data inválida.
- **Mesmo lugar:** coordenadas arredondadas a 4 casas (~11 m) + tipo formam um ponto; 17% dos pontos têm mais de
  um pedido. Na lista de atrasos, pontos da mesma rua com o mesmo tipo de problema viram uma linha só.

## Canais oficiais (conferidos em 14/11/2026)

| Canal | Fonte |
|---|---|
| Portal SP156 (sp156.prefeitura.sp.gov.br/portal), aplicativo SP156, telefone 156 | [Secretaria das Subprefeituras – Calçadas](https://prefeitura.sp.gov.br/web/subprefeituras/w/calcadas/37497) |
| WhatsApp (Chat SP156): (11) 3230-5156 | [Notícia da Prefeitura, 10/10/2023](https://prefeitura.sp.gov.br/noticia/prefeitura-lanca-servico-do-156-pelo-whatsapp-para-agilizar-atendimento-a-populacao) |
| O que incluir no pedido (endereço, referência, data, foto) | [Subprefeitura Ipiranga – tapa-buraco](https://prefeitura.sp.gov.br/web/ipiranga/w/opera%C3%A7%C3%A3o-tapa-buraco-no-ipiranga-saiba-como-solicitar-o-servi%C3%A7o) |
| Calçada em frente a imóvel é responsabilidade do proprietário | [Subprefeitura Ipiranga](https://prefeitura.sp.gov.br/web/ipiranga/w/a-responsabilidade-da-manuten%C3%A7%C3%A3o-das-cal%C3%A7adas-%C3%A9-de-responsabilidade-do-propriet%C3%A1rio) |

### Página de cada serviço no portal (conferido em 16/11/2026)

O portal do SP156 dá um endereço por serviço, `…/portal/servicos/informacao?servico=<id>`, então o app leva o
cidadão direto à página certa em vez da home. Os ids em `config.SERVICOS_PORTAL` foram conferidos um a um:
a página responde 200 e o título é exatamente o nome do serviço.

| Serviço | Página oficial |
|---|---|
| Tapa-buraco | [952](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=952) |
| Tapa-buraco em faixa exclusiva ou corredor de ônibus | [3170](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=3170) |
| Calçada pública - solicitar manutenção | [931](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=931) |
| Calçada particular - denunciar calçada danificada ou inexistente | [906](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=906) |
| Guias para travessia de pedestres - Solicitar rebaixamento | [766](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=766) |
| Guia rebaixada - solicitar fiscalização de rebaixamento irregular | [919](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=919) |
| Entulho e grandes objetos em via pública - solicitar remoção | [2641](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=2641) |
| Denunciar descarte irregular de entulho e outros resíduos em área pública | [915](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=915) |
| Denunciar caçamba irregular de entulho de construção | [751](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=751) |
| Fazer reclamação de falta de varrição | [945](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=945) |
| Sacos de varrição - Fazer reclamação de falta de remoção | [946](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=946) |

Faltam dois dos treze: "Acessibilidade - solicitar avaliação de obstáculo na calçada" e "Sugerir construção de
calçadas em áreas públicas e praças". Não achamos o id deles e **não inventamos**: nesses dois casos o app
mostra o nome exato do serviço e manda para o portal geral, como antes.
