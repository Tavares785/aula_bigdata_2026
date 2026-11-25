-- Missao 2.3 - SUA VEZ: crie as 6 views abaixo (camada gold) e depois
-- conecte-as ao dashboard. Siga o modelo de 02_views_prontas.sql.
-- Cada view alimenta um grafico do dashboard. Os nomes das colunas abaixo sao
-- OBRIGATORIOS (o professor confere). Rode cada CREATE separadamente.
--
-- Dicas de sintaxe do Athena (Trino): date_trunc('week', col), CASE WHEN,
-- COUNT(DISTINCT col), ROUND(x, 2), AVG(CASE WHEN ... THEN 1.0 ELSE 0.0 END).

-- ---------------------------------------------------------------------------
-- A) vw_atraso_nota  ->  grafico de barras: o atraso derruba a nota?
--    Colunas: faixa_atraso, avaliacoes, nota_media
--    faixa_atraso: '0 - no prazo', '1-3 dias', '4-7 dias', '8+ dias'
--    (use CASE sobre atraso_dias; considere so itens entregues COM nota)
--    Dica: para ordenar as faixas no grafico, voce pode prefixar: '1) ...'
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_nota AS
SELECT CASE
         WHEN atraso_dias <= 0 THEN '1) 0 - no prazo'
         WHEN atraso_dias <= 3 THEN '2) 1-3 dias'
         WHEN atraso_dias <= 7 THEN '3) 4-7 dias'
         ELSE '4) 8+ dias'
       END                                  AS faixa_atraso,
       COUNT(*)                             AS avaliacoes,
       ROUND(AVG(nota_avaliacao * 1.0), 2)  AS nota_media
FROM pedidos
WHERE status_pedido = 'entregue'
  AND nota_avaliacao IS NOT NULL
  AND atraso_dias IS NOT NULL
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- B) vw_problemas_categoria  ->  barras empilhadas / ranking de problemas
--    Colunas: categoria, canal, itens, pct_cancelado, pct_devolvido
--    pct_* = 100 * proporcao de itens com aquele status (use TODOS os status)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_problemas_categoria AS
SELECT categoria,
       canal,
       COUNT(*)                                                                    AS itens,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'cancelado' THEN 1.0 ELSE 0.0 END), 2) AS pct_cancelado,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'devolvido' THEN 1.0 ELSE 0.0 END), 2) AS pct_devolvido
FROM pedidos
GROUP BY 1, 2;


-- ---------------------------------------------------------------------------
-- C) vw_serie_diaria  ->  serie temporal (Black Friday e Natal aparecem?)
--    Colunas: dia, pedidos, receita, ticket_medio
--    ticket_medio = receita / pedidos distintos do dia (so itens entregues)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_serie_diaria AS
SELECT data_pedido                                              AS dia,
       COUNT(DISTINCT pedido_id)                                AS pedidos,
       ROUND(SUM(valor_total), 2)                               AS receita,
       ROUND(SUM(valor_total) / COUNT(DISTINCT pedido_id), 2)   AS ticket_medio
FROM pedidos
WHERE status_pedido = 'entregue'
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- D) vw_kpis  ->  "Big Numbers" no topo do dashboard (UMA unica linha)
--    Colunas: receita_total, pedidos, ticket_medio, pct_itens_atrasados,
--             nota_media, pct_cancelado_devolvido
--    Atencao ao denominador de cada metrica: receita/ticket/atraso/nota usam
--    itens entregues; pct_cancelado_devolvido usa todos os itens.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_kpis AS
SELECT ROUND(SUM(CASE WHEN status_pedido = 'entregue' THEN valor_total END), 2)            AS receita_total,
       COUNT(DISTINCT CASE WHEN status_pedido = 'entregue' THEN pedido_id END)             AS pedidos,
       ROUND(SUM(CASE WHEN status_pedido = 'entregue' THEN valor_total END)
             / COUNT(DISTINCT CASE WHEN status_pedido = 'entregue' THEN pedido_id END), 2) AS ticket_medio,
       ROUND(100.0 * SUM(CASE WHEN status_pedido = 'entregue' AND atraso_dias > 0 THEN 1 ELSE 0 END)
             / SUM(CASE WHEN status_pedido = 'entregue' THEN 1 ELSE 0 END), 1)             AS pct_itens_atrasados,
       ROUND(AVG(CASE WHEN status_pedido = 'entregue' THEN nota_avaliacao * 1.0 END), 2)  AS nota_media,
       ROUND(100.0 * AVG(CASE WHEN status_pedido IN ('cancelado', 'devolvido')
                              THEN 1.0 ELSE 0.0 END), 1)                                   AS pct_cancelado_devolvido
FROM pedidos;


-- ---------------------------------------------------------------------------
-- E) vw_atraso_chuva  ->  a chuva explica o atraso? (JOIN com chuva_diaria)
--    Junte pedidos e chuva_diaria por cidade e data_pedido = dia.
--    Colunas: faixa_chuva, itens, atraso_medio_dias, pct_atrasados
--    faixa_chuva (use chuva_3d_mm = chuva do dia do pedido + 2 dias seguintes):
--      '1) sem chuva (<5 mm)', '2) fraca (5-20)', '3) forte (20-40)',
--      '4) muito forte (40+)'
--    So itens entregues. Depois pergunte: o efeito e da chuva ou da regiao?
--    (Manaus e Belem chovem muito.) Teste a view tambem por regiao.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_chuva AS
SELECT CASE
         WHEN c.chuva_3d_mm < 5  THEN '1) sem chuva (<5 mm)'
         WHEN c.chuva_3d_mm < 20 THEN '2) fraca (5-20)'
         WHEN c.chuva_3d_mm < 40 THEN '3) forte (20-40)'
         ELSE '4) muito forte (40+)'
       END                                                                   AS faixa_chuva,
       COUNT(*)                                                              AS itens,
       ROUND(AVG(p.atraso_dias * 1.0), 2)                                    AS atraso_medio_dias,
       ROUND(100.0 * AVG(CASE WHEN p.atraso_dias > 0 THEN 1.0 ELSE 0.0 END), 1) AS pct_atrasados
FROM pedidos p
JOIN chuva_diaria c
  ON p.cidade = c.cidade AND p.data_pedido = c.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;

-- E2) Complemento de E: o efeito e da chuva ou da regiao? Mesma regra de
--     faixa_chuva, quebrada por regiao. Alimenta um grafico de barras agrupadas.
CREATE OR REPLACE VIEW vw_atraso_chuva_regiao AS
SELECT p.regiao,
       CASE
         WHEN c.chuva_3d_mm < 5  THEN '1) sem chuva (<5 mm)'
         WHEN c.chuva_3d_mm < 20 THEN '2) fraca (5-20)'
         WHEN c.chuva_3d_mm < 40 THEN '3) forte (20-40)'
         ELSE '4) muito forte (40+)'
       END                                                                   AS faixa_chuva,
       COUNT(*)                                                              AS itens,
       ROUND(AVG(p.atraso_dias * 1.0), 2)                                    AS atraso_medio_dias,
       ROUND(100.0 * AVG(CASE WHEN p.atraso_dias > 0 THEN 1.0 ELSE 0.0 END), 1) AS pct_atrasados
FROM pedidos p
JOIN chuva_diaria c
  ON p.cidade = c.cidade AND p.data_pedido = c.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1, 2;


-- ---------------------------------------------------------------------------
-- F) vw_feriados  ->  feriado muda a operacao? (JOIN com feriados)
--    Dica: LEFT JOIN (SELECT DISTINCT dia FROM feriados) f ON p.data_pedido = f.dia
--    Colunas: tipo_dia ('feriado' ou 'dia comum'), dias, pedidos,
--             pedidos_por_dia, atraso_medio_dias
--    dias = COUNT(DISTINCT data_pedido); so itens entregues.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_feriados AS
SELECT CASE WHEN f.dia IS NOT NULL THEN 'feriado' ELSE 'dia comum' END        AS tipo_dia,
       COUNT(DISTINCT p.data_pedido)                                          AS dias,
       COUNT(DISTINCT p.pedido_id)                                            AS pedidos,
       ROUND(1.0 * COUNT(DISTINCT p.pedido_id) / COUNT(DISTINCT p.data_pedido), 2) AS pedidos_por_dia,
       ROUND(AVG(p.atraso_dias * 1.0), 2)                                     AS atraso_medio_dias
FROM pedidos p
LEFT JOIN (SELECT DISTINCT dia FROM feriados) f
  ON p.data_pedido = f.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- BONUS) Crie uma 5a view que responda a uma pergunta SUA (ex.: perfil por
--    cliente_segmento, efeito do desconto, forma_pagamento x parcelas,
--    transportadora x nota). Explique no FINAL_REPORT.md.
-- ---------------------------------------------------------------------------

-- Pergunta do grupo: a transportadora explica atraso, nota e devolucao?
-- Usa todos os status para pct_devolvido; atraso e nota so dos entregues.
CREATE OR REPLACE VIEW vw_transportadora AS
SELECT transportadora,
       regiao,
       COUNT(*)                                                                         AS itens,
       ROUND(AVG(CASE WHEN status_pedido = 'entregue' THEN atraso_dias * 1.0 END), 2)  AS atraso_medio_dias,
       ROUND(100.0 * SUM(CASE WHEN status_pedido = 'entregue' AND atraso_dias > 0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN status_pedido = 'entregue' THEN 1 ELSE 0 END), 0), 1) AS pct_atrasados,
       ROUND(AVG(CASE WHEN status_pedido = 'entregue' THEN nota_avaliacao * 1.0 END), 2) AS nota_media,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'devolvido' THEN 1.0 ELSE 0.0 END), 2) AS pct_devolvido
FROM pedidos
GROUP BY 1, 2;
