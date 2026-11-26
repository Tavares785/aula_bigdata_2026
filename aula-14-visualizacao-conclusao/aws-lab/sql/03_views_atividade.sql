-- Aula 14 — MercadoFacil — RA 6325192
-- Athena (Trino), banco mercadofacil_aula14.
-- Execute cada CREATE OR REPLACE VIEW separadamente no editor do Athena.
-- Fonte: pedidos; chuva_diaria; feriados (material fornecido pelo professor).
-- Convencao: receita e atrasos da base de itens entregues.

-- A) Avaliacao por faixa de atraso (entregues com avaliacao e prazo conhecido)
CREATE OR REPLACE VIEW vw_atraso_nota AS
SELECT
    CASE
        WHEN atraso_dias = 0 THEN '0 - no prazo'
        WHEN atraso_dias BETWEEN 1 AND 3 THEN '1-3 dias'
        WHEN atraso_dias BETWEEN 4 AND 7 THEN '4-7 dias'
        ELSE '8+ dias'
    END AS faixa_atraso,
    COUNT(*) AS avaliacoes,
    ROUND(AVG(CAST(nota_avaliacao AS DOUBLE)), 2) AS nota_media
FROM pedidos
WHERE status_pedido = 'entregue'
  AND nota_avaliacao IS NOT NULL
  AND atraso_dias IS NOT NULL
GROUP BY 1;

-- B) Cancelamentos e devolucoes por categoria e canal (todos os itens)
CREATE OR REPLACE VIEW vw_problemas_categoria AS
SELECT
    categoria,
    canal,
    COUNT(*) AS itens,
    ROUND(100.0 * COUNT_IF(status_pedido = 'cancelado') / COUNT(*), 2) AS pct_cancelado,
    ROUND(100.0 * COUNT_IF(status_pedido = 'devolvido') / COUNT(*), 2) AS pct_devolvido
FROM pedidos
GROUP BY 1, 2;

-- C) Serie diaria de vendas (somente itens entregues)
CREATE OR REPLACE VIEW vw_serie_diaria AS
SELECT
    data_pedido AS dia,
    COUNT(DISTINCT pedido_id) AS pedidos,
    ROUND(SUM(valor_total), 2) AS receita,
    ROUND(SUM(valor_total) / NULLIF(COUNT(DISTINCT pedido_id), 0), 2) AS ticket_medio
FROM pedidos
WHERE status_pedido = 'entregue'
GROUP BY 1;

-- D) Indicadores consolidados em uma unica linha
CREATE OR REPLACE VIEW vw_kpis AS
SELECT
    ROUND(SUM(CASE WHEN status_pedido = 'entregue' THEN valor_total ELSE 0 END), 2) AS receita_total,
    COUNT(DISTINCT CASE WHEN status_pedido = 'entregue' THEN pedido_id END) AS pedidos,
    ROUND(
        SUM(CASE WHEN status_pedido = 'entregue' THEN valor_total ELSE 0 END)
        / NULLIF(COUNT(DISTINCT CASE WHEN status_pedido = 'entregue' THEN pedido_id END), 0), 2
    ) AS ticket_medio,
    ROUND(100.0 * COUNT_IF(status_pedido = 'entregue' AND atraso_dias > 0)
        / NULLIF(COUNT_IF(status_pedido = 'entregue' AND atraso_dias IS NOT NULL), 0), 2) AS pct_itens_atrasados,
    ROUND(AVG(CASE WHEN status_pedido = 'entregue' THEN CAST(nota_avaliacao AS DOUBLE) END), 2) AS nota_media,
    ROUND(100.0 * COUNT_IF(status_pedido IN ('cancelado', 'devolvido'))
        / NULLIF(COUNT(*), 0), 2) AS pct_cancelado_devolvido
FROM pedidos;

-- E) Precipitacao e atraso: associacao descritiva, nao causalidade
CREATE OR REPLACE VIEW vw_atraso_chuva AS
SELECT
    CASE
        WHEN c.chuva_3d_mm < 5 THEN '1) sem chuva (<5 mm)'
        WHEN c.chuva_3d_mm < 20 THEN '2) fraca (5-20)'
        WHEN c.chuva_3d_mm < 40 THEN '3) forte (20-40)'
        ELSE '4) muito forte (40+)'
    END AS faixa_chuva,
    COUNT(*) AS itens,
    ROUND(AVG(CAST(p.atraso_dias AS DOUBLE)), 2) AS atraso_medio_dias,
    ROUND(100.0 * COUNT_IF(p.atraso_dias > 0)
        / NULLIF(COUNT_IF(p.atraso_dias IS NOT NULL), 0), 2) AS pct_atrasados
FROM pedidos p
JOIN chuva_diaria c
  ON p.cidade = c.cidade AND p.data_pedido = c.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;

-- F) Dias com feriado e dias comuns: contagem de pedidos por dia
CREATE OR REPLACE VIEW vw_feriados AS
SELECT
    CASE WHEN f.dia IS NOT NULL THEN 'feriado' ELSE 'dia comum' END AS tipo_dia,
    COUNT(DISTINCT p.data_pedido) AS dias,
    COUNT(DISTINCT p.pedido_id) AS pedidos,
    ROUND(
        1.0 * COUNT(DISTINCT p.pedido_id) / NULLIF(COUNT(DISTINCT p.data_pedido), 0), 2
    ) AS pedidos_por_dia,
    ROUND(AVG(CAST(p.atraso_dias AS DOUBLE)), 2) AS atraso_medio_dias
FROM pedidos p
LEFT JOIN (SELECT DISTINCT dia FROM feriados) f
  ON p.data_pedido = f.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;
