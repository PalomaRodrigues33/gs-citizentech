-- Pergunta do cidadão: "Onde a Prefeitura está mais atrasada perto de mim?"
-- Funções de janela: ROW_NUMBER() OVER (posição no recorte) e PERCENT_RANK() OVER (posição na cidade inteira).
-- Parâmetros: :subprefeitura, :grupo (NULL = todos), :limite
WITH cidade AS (
    SELECT *, ROUND(100 * (1 - PERCENT_RANK() OVER (ORDER BY dias_de_espera DESC)), 0) AS percentil_cidade
    FROM lista_atrasos
)
SELECT ROW_NUMBER() OVER (ORDER BY dias_de_espera DESC, dias_em_aberto DESC) AS posicao,
       problema_id, grupo, servico, subprefeitura, distrito, logradouro, lat, lon, pontos,
       pedidos_abertos, data_abertura, dias_em_aberto, dias_de_espera, mediana_tipica_dias,
       vezes_acima_do_tipico, percentil_cidade
FROM cidade
WHERE (:subprefeitura IS NULL OR subprefeitura = :subprefeitura)
  AND (:grupo IS NULL OR grupo = :grupo)
ORDER BY posicao
LIMIT :limite;
