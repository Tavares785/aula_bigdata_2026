-- Consultas de validacao/negocio no Athena (database mercadofacil_db).

-- 1) Conferencia de volumes: raw = silver + quarentena
SELECT 'silver' AS camada, count(*) AS linhas FROM pedidos_itens
UNION ALL
SELECT 'quarentena', count(*) FROM quarentena;

-- 2) Motivos de quarentena
SELECT motivo, count(*) AS linhas
FROM quarentena
CROSS JOIN UNNEST(split(motivo_quarentena, chr(59))) AS t(motivo)
GROUP BY motivo
ORDER BY linhas DESC;

-- 3) Atraso x nota: quanto maior o atraso, pior a avaliacao?
SELECT faixa_atraso, itens_entregues, nota_media, pct_nota_1_ou_2
FROM atraso_vs_nota
ORDER BY faixa_atraso;

-- 4) Atraso por regiao (Norte/Nordeste x resto)
SELECT regiao,
       sum(pedidos_entregues) AS pedidos,
       round(100.0 * sum(pedidos_atrasados) / sum(pedidos_entregues), 1) AS pct_atrasados
FROM entregas_estado_mes
GROUP BY regiao
ORDER BY pct_atrasados DESC;

-- 5) Transportadora x CD com mais atraso
SELECT transportadora, centro_distribuicao, pedidos_entregues, pct_atrasados, atraso_medio_dias
FROM atraso_transportadora_cd
ORDER BY pct_atrasados DESC
LIMIT 8;

-- 6) Sazonalidade: receita e atraso por mes (Black Friday / Natal)
SELECT ano_mes, periodo,
       round(sum(receita_bruta), 2) AS receita_bruta,
       round(avg(pct_itens_atrasados), 1) AS pct_itens_atrasados
FROM vendas_mensais_categoria
GROUP BY ano_mes, periodo
ORDER BY ano_mes;

-- 7) Cancelamento e devolucao por categoria
SELECT categoria,
       sum(itens) AS itens,
       round(100.0 * sum(itens_cancelados) / sum(itens), 1) AS pct_cancelados,
       round(100.0 * sum(itens_devolvidos) / sum(itens), 1) AS pct_devolvidos,
       round(sum(receita_perdida), 2) AS receita_perdida
FROM cancelamento_devolucao
GROUP BY categoria
ORDER BY receita_perdida DESC;
