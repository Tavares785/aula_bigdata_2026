-- Missao 2.1 - Conferir a carga (rode UMA consulta por vez no Athena).
-- Antes: selecione o workgroup "wg-..." (output do terraform) e o banco
-- "mercadofacil_aula14".

-- 1) Quantas linhas? (esperado: 10000)
SELECT COUNT(*) AS linhas FROM pedidos;

-- 2) Amostra
SELECT * FROM pedidos LIMIT 10;

-- 3) Quantos pedidos, clientes e SKUs distintos?
SELECT COUNT(DISTINCT pedido_id)  AS pedidos,
       COUNT(DISTINCT cliente_id) AS clientes,
       COUNT(DISTINCT sku)        AS skus,
       MIN(data_pedido)           AS primeira_data,
       MAX(data_pedido)           AS ultima_data
FROM pedidos;

-- 4) Distribuicao por status (entregue / cancelado / devolvido)
SELECT status_pedido, COUNT(*) AS itens
FROM pedidos
GROUP BY status_pedido
ORDER BY itens DESC;

-- 5) Onde ha nulos? (cancelados nao tem entrega/nota; nem todo cliente avalia)
SELECT COUNT_IF(atraso_dias    IS NULL) AS sem_atraso,
       COUNT_IF(nota_avaliacao IS NULL) AS sem_nota,
       COUNT_IF(data_entrega   IS NULL) AS sem_data_entrega
FROM pedidos;

-- 6) Tabelas de apoio (APIs publicas): chuva por cidade/dia e feriados 2025
SELECT * FROM chuva_diaria WHERE cidade = 'Manaus' ORDER BY dia LIMIT 10;
SELECT * FROM feriados ORDER BY dia;

-- 7) O JOIN casa? (cidade + dia do pedido). Esperado: 10000 linhas, 0 sem chuva
SELECT COUNT(*) AS itens, COUNT_IF(c.chuva_3d_mm IS NULL) AS sem_chuva
FROM pedidos p
LEFT JOIN chuva_diaria c ON p.cidade = c.cidade AND p.data_pedido = c.dia;
