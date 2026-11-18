-- Aula 12 - Consultas de verificação no Athena (camada gold)
-- Executar após o Glue Job SUCCEEDED e o Glue Crawler rodar.

-- 1) Amostra da fato de entregas (por item de pedido)
SELECT * FROM mercadofacil_db.fato_entregas LIMIT 10;

-- 2) Relação atraso x nota (pergunta de negócio principal)
SELECT faixa_atraso, itens, nota_media, taxa_atraso, prazo_medio_dias
FROM mercadofacil_db.agregado_atraso_nota
ORDER BY faixa_atraso;

-- 3) Sazonalidade: receita e atraso médio por mês e canal
SELECT ano_mes, canal_v, pedidos, receita_total,
       cancelamentos_devolucoes, atraso_medio_dias
FROM mercadofacil_db.sazonalidade_mensal
ORDER BY ano_mes, canal_v;

-- 4) Auditoria da quarentena (linhas rejeitadas e o motivo)
SELECT motivo, count(*) AS linhas
FROM mercadofacil_db.quarentena
GROUP BY motivo
ORDER BY linhas DESC;
