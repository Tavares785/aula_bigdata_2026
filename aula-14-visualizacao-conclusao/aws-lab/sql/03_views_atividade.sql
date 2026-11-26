-- Missao 2.3 - Views gold da atividade (camada gold sobre as tabelas
-- pedidos, chuva_diaria e feriados do banco mercadofacil_aula14).
-- Rode cada CREATE separadamente no Athena (workgroup do output do terraform).
-- Cada view alimenta um grafico do dashboard.
--
-- Convencao: "receita" = soma de valor_total dos itens ENTREGUES.
-- "Atrasado" = atraso_dias > 0.

-- ---------------------------------------------------------------------------
-- A) vw_atraso_nota -> barras: o atraso derruba a nota?
--    So itens entregues COM nota e atraso conhecidos.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_nota AS
SELECT CASE
         WHEN atraso_dias <= 0 THEN '0 - no prazo'
         WHEN atraso_dias <= 3 THEN '1-3 dias'
         WHEN atraso_dias <= 7 THEN '4-7 dias'
         ELSE '8+ dias'
       END                         AS faixa_atraso,
       COUNT(*)                    AS avaliacoes,
       ROUND(AVG(nota_avaliacao), 2) AS nota_media
FROM pedidos
WHERE status_pedido = 'entregue'
  AND nota_avaliacao IS NOT NULL
  AND atraso_dias IS NOT NULL
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- B) vw_problemas_categoria -> barras empilhadas: cancelamento e devolucao
--    Usa TODOS os status (o denominador e o total de itens do grupo).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_problemas_categoria AS
SELECT categoria,
       canal,
       COUNT(*) AS itens,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'cancelado' THEN 1.0 ELSE 0.0 END), 2) AS pct_cancelado,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'devolvido' THEN 1.0 ELSE 0.0 END), 2) AS pct_devolvido
FROM pedidos
GROUP BY 1, 2;


-- ---------------------------------------------------------------------------
-- C) vw_serie_diaria -> serie temporal (Black Friday e Natal aparecem?)
--    So itens entregues. ticket_medio = receita / pedidos distintos do dia.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_serie_diaria AS
SELECT data_pedido                        AS dia,
       COUNT(DISTINCT pedido_id)          AS pedidos,
       ROUND(SUM(valor_total), 2)         AS receita,
       ROUND(SUM(valor_total) / COUNT(DISTINCT pedido_id), 2) AS ticket_medio
FROM pedidos
WHERE status_pedido = 'entregue'
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- D) vw_kpis -> Big Numbers (UMA unica linha)
--    receita, pedidos, ticket, atraso e nota usam itens ENTREGUES.
--    pct_cancelado_devolvido usa TODOS os itens.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_kpis AS
SELECT e.receita_total,
       e.pedidos,
       ROUND(e.receita_total / e.pedidos, 2) AS ticket_medio,
       e.pct_itens_atrasados,
       e.nota_media,
       t.pct_cancelado_devolvido
FROM (
  SELECT ROUND(SUM(valor_total), 2)        AS receita_total,
         COUNT(DISTINCT pedido_id)         AS pedidos,
         ROUND(100.0 * AVG(CASE WHEN atraso_dias > 0 THEN 1.0
                                WHEN atraso_dias IS NOT NULL THEN 0.0 END), 2) AS pct_itens_atrasados,
         ROUND(AVG(nota_avaliacao), 2)     AS nota_media
  FROM pedidos
  WHERE status_pedido = 'entregue'
) e
CROSS JOIN (
  SELECT ROUND(100.0 * AVG(CASE WHEN status_pedido IN ('cancelado', 'devolvido')
                                THEN 1.0 ELSE 0.0 END), 2) AS pct_cancelado_devolvido
  FROM pedidos
) t;


-- ---------------------------------------------------------------------------
-- E) vw_atraso_chuva -> a chuva explica o atraso? (JOIN com chuva_diaria)
--    chuva_3d_mm = chuva do dia do pedido + 2 dias seguintes. So entregues.
--    Cuidado: o efeito pode ser da regiao (Norte chove mais), nao so da chuva.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_chuva AS
SELECT CASE
         WHEN c.chuva_3d_mm < 5  THEN '1) sem chuva (<5 mm)'
         WHEN c.chuva_3d_mm < 20 THEN '2) fraca (5-20)'
         WHEN c.chuva_3d_mm < 40 THEN '3) forte (20-40)'
         ELSE '4) muito forte (40+)'
       END                                   AS faixa_chuva,
       COUNT(*)                              AS itens,
       ROUND(AVG(p.atraso_dias), 2)          AS atraso_medio_dias,
       ROUND(100.0 * AVG(CASE WHEN p.atraso_dias > 0 THEN 1.0 ELSE 0.0 END), 1) AS pct_atrasados
FROM pedidos p
JOIN chuva_diaria c
  ON p.cidade = c.cidade AND p.data_pedido = c.dia
WHERE p.status_pedido = 'entregue'
  AND p.atraso_dias IS NOT NULL
  AND c.chuva_3d_mm IS NOT NULL
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- F) vw_feriados -> feriado muda a operacao? (JOIN com feriados)
--    dias = dias distintos de pedido. So itens entregues.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_feriados AS
SELECT CASE WHEN f.dia IS NOT NULL THEN 'feriado' ELSE 'dia comum' END AS tipo_dia,
       COUNT(DISTINCT p.data_pedido)                                  AS dias,
       COUNT(DISTINCT p.pedido_id)                                    AS pedidos,
       ROUND(1.0 * COUNT(DISTINCT p.pedido_id) / COUNT(DISTINCT p.data_pedido), 2) AS pedidos_por_dia,
       ROUND(AVG(p.atraso_dias), 2)                                   AS atraso_medio_dias
FROM pedidos p
LEFT JOIN (SELECT DISTINCT dia FROM feriados) f
  ON p.data_pedido = f.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- BONUS) vw_desconto_problemas -> o desconto reduz cancelamento/devolucao
--    ou so corta a receita? Pergunta do grupo, explicada no FINAL_REPORT.md.
--    Todos os status; ticket_medio considera so itens entregues.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_desconto_problemas AS
SELECT CASE
         WHEN desconto_pct = 0  THEN '1) sem desconto'
         WHEN desconto_pct <= 10 THEN '2) ate 10%'
         WHEN desconto_pct <= 20 THEN '3) 11-20%'
         ELSE '4) acima de 20%'
       END                                                           AS faixa_desconto,
       COUNT(*)                                                      AS itens,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'cancelado' THEN 1.0 ELSE 0.0 END), 2) AS pct_cancelado,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'devolvido' THEN 1.0 ELSE 0.0 END), 2) AS pct_devolvido,
       ROUND(AVG(CASE WHEN status_pedido = 'entregue' THEN valor_total END), 2)           AS valor_medio_item
FROM pedidos
GROUP BY 1;
