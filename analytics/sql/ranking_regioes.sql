-- Pergunta do cidadão: "Como a minha região se compara com as outras?"
-- Funções de janela: RANK() OVER, NTILE(3) OVER (terço: rápidas, meio, lentas), COUNT() OVER () e SUM() OVER ().
-- Parâmetro: :grupo (NULL = todos). Regiões com menos de 20 pedidos com resultado ficam de fora (ruído).
WITH r AS (
    SELECT subprefeitura, COUNT(*) AS pedidos, AVG(resolvido_7d) AS taxa_7d
    FROM pedidos
    WHERE subprefeitura IS NOT NULL AND subprefeitura NOT LIKE '%nao encontrada%'
      -- Órgãos executores não são região (config.ORGAOS_NAO_REGIAO): apareciam no ranking como se fossem bairro.
      AND subprefeitura NOT IN ('Superintendencia das Usinas de Asfalto',
                                'Departamento de Estradas de Rodagem',
                                'Secretaria Municipal do Verde e do Meio Ambiente')
      AND (:grupo IS NULL OR grupo = :grupo)
    GROUP BY subprefeitura
    HAVING SUM(CASE WHEN resolvido_7d IS NOT NULL THEN 1 ELSE 0 END) >= 20
)
SELECT RANK() OVER (ORDER BY taxa_7d DESC)              AS posicao,
       NTILE(3) OVER (ORDER BY taxa_7d DESC)              AS terco,
       COUNT(*) OVER ()                                   AS total_regioes,
       subprefeitura,
       pedidos,
       ROUND(100.0 * pedidos / SUM(pedidos) OVER (), 1)   AS participacao_pct,
       ROUND(100 * taxa_7d, 1)                            AS resolvidos_7d_pct
FROM r
ORDER BY posicao;
