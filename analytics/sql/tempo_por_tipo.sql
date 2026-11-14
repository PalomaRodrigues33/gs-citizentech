-- Pergunta do cidadão: "Quanto tempo esse tipo de problema leva na minha região, comparado com a cidade?"
-- Funções de janela: ROW_NUMBER() e COUNT() OVER (PARTITION BY ...) para a mediana (o SQLite não tem MEDIAN).
-- Parâmetro: :subprefeitura (NULL = só a cidade)
WITH escopos AS (
    SELECT 'cidade' AS escopo, grupo, dias_ate_resolver, resolvido_7d FROM pedidos
    UNION ALL
    SELECT 'regiao', grupo, dias_ate_resolver, resolvido_7d FROM pedidos WHERE subprefeitura = :subprefeitura
),
ordenado AS (
    SELECT escopo, grupo, dias_ate_resolver AS d,
           ROW_NUMBER() OVER (PARTITION BY escopo, grupo ORDER BY dias_ate_resolver) AS rn,
           COUNT(*)     OVER (PARTITION BY escopo, grupo)                           AS n
    FROM escopos
    WHERE dias_ate_resolver IS NOT NULL
),
mediana AS (
    SELECT escopo, grupo, AVG(d) AS mediana_dias
    FROM ordenado WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
    GROUP BY escopo, grupo
),
taxa AS (
    SELECT escopo, grupo, COUNT(*) AS pedidos,
           AVG(resolvido_7d) AS taxa_7d,
           SUM(CASE WHEN resolvido_7d IS NOT NULL THEN 1 ELSE 0 END) AS com_resultado
    FROM escopos GROUP BY escopo, grupo
)
SELECT t.escopo, t.grupo, t.pedidos, t.com_resultado,
       ROUND(100 * t.taxa_7d, 1) AS resolvidos_7d_pct,
       m.mediana_dias
FROM taxa t LEFT JOIN mediana m ON m.escopo = t.escopo AND m.grupo = t.grupo
ORDER BY t.escopo, resolvidos_7d_pct;
