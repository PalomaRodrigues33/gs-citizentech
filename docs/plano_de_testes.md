# Plano de testes

Execução: `python -m pytest -v` (ou `docker compose --profile test run --rm tests`).
**Evidência para o PDF:** print do terminal com `41 passed`.

A suíte roda offline: o `conftest.py` força o assistente de regras (`LLM_PROVIDER=mock`), então os testes
não dependem de chave de API nem de rede, e passam igual na máquina do avaliador e no CI.

Os testes de API (CT-29 a CT-37) usam os dados reais gerados por `python run_all.py`; sem eles, são ignorados
(aparecem como `skipped`). Nos testes, a IA não grava exemplos na camada gold.

| ID | Módulo | Caso | Resultado esperado |
|---|---|---|---|
| CT-01 | ingestão | Classificação dos 5 grupos de zeladoria | Cada serviço no grupo certo |
| CT-02 | ingestão | Poda de árvore "em calçadas" e fiação na calçada | **Não** são calçada |
| CT-03 | ingestão | Serviço nulo, NaN ou fora do escopo | Fora do recorte |
| CT-04 | ingestão | Grava bronze e relatório | 3 de 4 linhas; contagem por grupo |
| CT-05 | ingestão | Arquivo sem as colunas obrigatórias | Erro com a lista de colunas |
| CT-06 | silver | Data de abertura inválida | Linha removida e contada |
| CT-07 | silver | Finalização antes da abertura | Data anulada |
| CT-08 | silver | Coordenada 0,0 e coordenada vazia | Coordenadas anuladas, linha mantida |
| CT-09 | silver | Alvo de 7 dias: 3 dias, 19 dias, em aberto | 1, 0, 0 |
| CT-10 | silver | Alvo desconhecido: aberto recente e cancelado | Vazio |
| CT-11 | silver | Pedidos no mesmo ponto e tipo | Contagem no ponto |
| CT-12 | silver | Grava CSV, `pedidos` e `qualidade_dados` | Contagens batem |
| CT-13 | modelo | Corte temporal; modelo supera a regra do tipo | AUC modelo > 0,8 > AUC regra; regra = 0,5 dentro do tipo |
| CT-14 | modelo | Risco por região | Região lenta > rápida + 0,3; valores entre 0 e 1 |
| CT-15 | atrasos | Mesma rua e tipo | Um problema, com 2 pontos e 2 pedidos |
| CT-16 | atrasos | Dias de espera | Soma de todos os pedidos abertos (10 + 5 = 15) |
| CT-17 | atrasos | Ordem e tempo típico | Mais esperado primeiro; 90 dias = 22,5× a mediana de 4 |
| CT-18 | SQL | Tempo por tipo, região x cidade | 75% e mediana 4 (`ROW_NUMBER`, `COUNT OVER`) |
| CT-19 | SQL | Tendência semanal | Ignora antes de 13/07; `LAG` = −50; média móvel = 75 |
| CT-20 | SQL | Ranking | Mínimo de 20 pedidos; `RANK`, `NTILE(3)`, participação soma 100% |
| CT-21 | SQL | Atrasos com filtro e limite | Ordenados; `LIMIT` parametrizado |
| CT-22 | IA | Parser: JSON em cerca de código; grupo no lugar de serviço; vazio | Aceita só serviço exato |
| CT-23 | IA | Saída com link de golpe, item inventado, tipos errados | Link removido; só itens da lista; padrões seguros |
| CT-24 | IA/segurança | Relato tenta fechar `</relato>` e injetar ordem | Marcas removidas; um único bloco |
| CT-25 | IA | LLM fora do ar (HTTP 429) ou fora do formato | Rascunho simples com o motivo |
| CT-26 | IA | Mensagens do prompt | 3 pares few-shot + relato marcado |
| CT-27 | IA | Linha de base nos 30 relatos rotulados | ≥ 75% no serviço exato; endereço presente não vira campo vazio |
| CT-28 | IA/privacidade | Registro de evidência | Só entrada limpa e saída, sem dado extra |
| CT-29 | API | Saúde e regiões | Dados prontos; 30+ subprefeituras |
| CT-30 | API | Região | 3 perguntas, cada uma com resposta em frase |
| CT-31 | API/segurança | Região, tipo e limite inválidos; `' OR 1=1 --` | 422 com mensagem |
| CT-32 | API | Atrasos | Ordenados por dias de espera |
| CT-33 | API | Assistente com relato de buraco | Serviço válido, chance 0–100, canais oficiais do código |
| CT-34 | API/validação | Relato curto, longo, distrito de outra região | 422 |
| CT-35 | API | Relato fora da zeladoria (semáforo) | "outro", sem previsão inventada |
| CT-36 | API/segurança | Limite de chamadas por IP | 4ª chamada recusada; outro IP passa; janela anda |
| CT-37 | API/segurança | Cabeçalhos | `nosniff`, `DENY`, CSP `default-src 'self'` |
| CT-38 | Segurança | Link da página do serviço no SP156 | Sai da `config`, domínio oficial; nome fora dos 13 não gera link |
| CT-39 | API/dados | Lista de regiões e bairros | Cada distrito em uma região só; nenhum órgão executor na lista |
| CT-40 | Segurança | Chave de API fora do código | Lê do `.env` (não versionado); variável de ambiente tem prioridade |
| CT-41 | IA | Rascunho por regras em todos os serviços | Os 13 serviços têm frase de abertura; nenhum relato rotulado cai no modo de erro |

## Teste de interface (evidência visual)

As capturas das 4 telas num iPhone 13 simulado, em modo claro e escuro, vão no PDF da entrega.
Para gerar de novo: `node scripts/capturas.js` com a API rodando.
