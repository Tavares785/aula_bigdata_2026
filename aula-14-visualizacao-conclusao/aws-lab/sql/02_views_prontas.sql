-- Missao 2.2 - Duas views (camada gold) JA PRONTAS, como exemplo.
-- Rode cada CREATE separadamente. Depois confira com SELECT * FROM <view> LIMIT 20.
--
-- Convencao do grupo: "receita" = soma de valor_total dos itens ENTREGUES.

-- Vendas por mes e categoria
CREATE OR REPLACE VIEW vw_vendas_mensal AS
SELECT date_trunc('month', data_pedido)              AS mes,
       categoria,
       COUNT(DISTINCT pedido_id)                     AS pedidos,
       SUM(quantidade)                               AS itens,
       ROUND(SUM(valor_total), 2)                    AS receita,
       ROUND(SUM(valor_total - custo_unitario * quantidade), 2) AS margem
FROM pedidos
WHERE status_pedido = 'entregue'
GROUP BY 1, 2;

-- Logistica por estado e transportadora
CREATE OR REPLACE VIEW vw_logistica_estado AS
SELECT estado,
       regiao,
       transportadora,
       COUNT(*)                                                  AS itens_entregues,
       ROUND(AVG(atraso_dias), 2)                                AS atraso_medio_dias,
       ROUND(100.0 * AVG(CASE WHEN atraso_dias > 0 THEN 1.0 ELSE 0.0 END), 1) AS pct_atrasados,
       ROUND(AVG(nota_avaliacao), 2)                             AS nota_media
FROM pedidos
WHERE status_pedido = 'entregue'
GROUP BY 1, 2, 3;
