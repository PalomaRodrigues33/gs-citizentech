-- Pergunta do cidadão: "Minha região está melhorando ou piorando?"
-- Funções de janela: AVG() OVER (ROWS BETWEEN 2 PRECEDING ...) = média móvel de 3 semanas; LAG() = variação semanal.
-- A partir de :inicio porque 01-12/07 teve quebra na série (ver README).
-- Parâmetros: :subprefeitura (NULL = só a cidade), :grupo (NULL = todos)
WITH semanal AS (
    SELECT strftime('%Y-%W', data_abertura) AS semana,
           MIN(data_abertura) AS inicio,
           AVG(CASE WHEN subprefeitura = :subprefeitura THEN resolvido_7d END) AS regiao,
           AVG(resolvido_7d) AS cidade,
           SUM(CASE WHEN subprefeitura = :subprefeitura THEN 1 ELSE 0 END) AS n_regiao
    FROM pedidos
    WHERE resolvido_7d IS NOT NULL AND data_abertura >= :inicio AND (:grupo IS NULL OR grupo = :grupo)
    GROUP BY semana
)
SELECT semana, inicio, n_regiao,
       ROUND(100 * regiao, 1) AS regiao_pct,
       ROUND(100 * cidade, 1) AS cidade_pct,
       ROUND(100 * AVG(regiao) OVER (ORDER BY semana ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS regiao_media_3sem,
       ROUND(100 * AVG(cidade) OVER (ORDER BY semana ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS cidade_media_3sem,
       ROUND(100 * (regiao - LAG(regiao) OVER (ORDER BY semana)), 1) AS regiao_variacao_pp
FROM semanal
ORDER BY semana;
