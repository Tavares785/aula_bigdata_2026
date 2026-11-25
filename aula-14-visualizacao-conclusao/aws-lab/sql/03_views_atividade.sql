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
-- CREATE OR REPLACE VIEW vw_atraso_nota AS
-- SELECT ...


-- ---------------------------------------------------------------------------
-- B) vw_problemas_categoria  ->  barras empilhadas / ranking de problemas
--    Colunas: categoria, canal, itens, pct_cancelado, pct_devolvido
--    pct_* = 100 * proporcao de itens com aquele status (use TODOS os status)
-- ---------------------------------------------------------------------------
-- CREATE OR REPLACE VIEW vw_problemas_categoria AS
-- SELECT ...


-- ---------------------------------------------------------------------------
-- C) vw_serie_diaria  ->  serie temporal (Black Friday e Natal aparecem?)
--    Colunas: dia, pedidos, receita, ticket_medio
--    ticket_medio = receita / pedidos distintos do dia (so itens entregues)
-- ---------------------------------------------------------------------------
-- CREATE OR REPLACE VIEW vw_serie_diaria AS
-- SELECT ...


-- ---------------------------------------------------------------------------
-- D) vw_kpis  ->  "Big Numbers" no topo do dashboard (UMA unica linha)
--    Colunas: receita_total, pedidos, ticket_medio, pct_itens_atrasados,
--             nota_media, pct_cancelado_devolvido
--    Atencao ao denominador de cada metrica: receita/ticket/atraso/nota usam
--    itens entregues; pct_cancelado_devolvido usa todos os itens.
-- ---------------------------------------------------------------------------
-- CREATE OR REPLACE VIEW vw_kpis AS
-- SELECT ...


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
-- CREATE OR REPLACE VIEW vw_atraso_chuva AS
-- SELECT ...


-- ---------------------------------------------------------------------------
-- F) vw_feriados  ->  feriado muda a operacao? (JOIN com feriados)
--    Dica: LEFT JOIN (SELECT DISTINCT dia FROM feriados) f ON p.data_pedido = f.dia
--    Colunas: tipo_dia ('feriado' ou 'dia comum'), dias, pedidos,
--             pedidos_por_dia, atraso_medio_dias
--    dias = COUNT(DISTINCT data_pedido); so itens entregues.
-- ---------------------------------------------------------------------------
-- CREATE OR REPLACE VIEW vw_feriados AS
-- SELECT ...


-- ---------------------------------------------------------------------------
-- BONUS) Crie uma 5a view que responda a uma pergunta SUA (ex.: perfil por
--    cliente_segmento, efeito do desconto, forma_pagamento x parcelas,
--    transportadora x nota). Explique no FINAL_REPORT.md.
-- ---------------------------------------------------------------------------
