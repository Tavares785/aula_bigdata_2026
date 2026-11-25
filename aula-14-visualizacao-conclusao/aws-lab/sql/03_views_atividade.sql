-- Missao 2.3 - Views da camada gold (Athena / Trino), banco mercadofacil_aula14.
-- Rode cada CREATE separadamente. Depois confira com SELECT * FROM <view> LIMIT 20.
--
-- Convencoes do grupo, validadas contra a base antes de escrever as views:
--   * "receita" = SUM(valor_total) dos itens com status_pedido = 'entregue';
--   * "atrasado" = atraso_dias > 0 (a base tem 0 como minimo, nunca negativo:
--     nenhuma entrega adiantada, conferido em 10.000 linhas);
--   * atraso_dias = prazo_real_dias - prazo_estimado_dias em 100% das linhas;
--   * itens 'cancelado' nao tem entrega nem nota (348 linhas, todas nulas), mas
--     itens 'devolvido' TEM atraso_dias (408) e quase sempre nota (372). Por isso
--     cada view declara explicitamente o filtro de status: deixar o 'devolvido'
--     entrar sem querer muda a nota media e o % de atraso.

-- ---------------------------------------------------------------------------
-- A) vw_atraso_nota  ->  grafico de barras: o atraso derruba a nota?
--    Colunas: faixa_atraso, avaliacoes, nota_media
--    So itens entregues COM nota. O prefixo '1)'..'4)' existe para o Superset
--    ordenar as faixas alfabeticamente em vez de embaralhar os rotulos.
--    Uso atraso_dias <= 0 na primeira faixa por robustez: se o dado passar a
--    ter entrega adiantada, ela entra em "no prazo" em vez de cair no ELSE
--    e ser contada como 8+ dias de atraso.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_nota AS
SELECT CASE
         WHEN atraso_dias <= 0            THEN '1) 0 - no prazo'
         WHEN atraso_dias BETWEEN 1 AND 3 THEN '2) 1-3 dias'
         WHEN atraso_dias BETWEEN 4 AND 7 THEN '3) 4-7 dias'
         ELSE                                  '4) 8+ dias'
       END                             AS faixa_atraso,
       COUNT(*)                        AS avaliacoes,
       ROUND(AVG(nota_avaliacao), 2)   AS nota_media
FROM pedidos
WHERE status_pedido = 'entregue'
  AND nota_avaliacao IS NOT NULL
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- B) vw_problemas_categoria  ->  barras empilhadas / ranking de problemas
--    Colunas: categoria, canal, itens, pct_cancelado, pct_devolvido
--    Usa TODOS os status: o denominador e o total de itens daquele cruzamento,
--    senao o percentual de cancelamento nao tem sentido.
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
-- C) vw_serie_diaria  ->  serie temporal (Black Friday e Natal aparecem?)
--    Colunas: dia, pedidos, receita, ticket_medio
--    ticket_medio = receita do dia / pedidos DISTINTOS do dia. Dividir pelo
--    numero de itens daria "preco medio do item", que e outra metrica.
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
--    Cada metrica tem seu proprio denominador, e por isso o filtro de status
--    vai DENTRO de cada agregacao, nao no WHERE: receita, ticket, atraso e nota
--    sao dos itens entregues; pct_cancelado_devolvido e sobre os 10.000 itens.
--    O AVG do Trino ignora NULL, o que faz o denominador de pct_itens_atrasados
--    ser so o dos entregues e o de nota_media so o dos entregues avaliados.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_kpis AS
SELECT ROUND(SUM(CASE WHEN status_pedido = 'entregue' THEN valor_total END), 2) AS receita_total,
       COUNT(DISTINCT CASE WHEN status_pedido = 'entregue' THEN pedido_id END)  AS pedidos,
       ROUND(SUM(CASE WHEN status_pedido = 'entregue' THEN valor_total END)
             / COUNT(DISTINCT CASE WHEN status_pedido = 'entregue' THEN pedido_id END), 2) AS ticket_medio,
       ROUND(100.0 * AVG(CASE WHEN status_pedido = 'entregue'
                              THEN (CASE WHEN atraso_dias > 0 THEN 1.0 ELSE 0.0 END) END), 2) AS pct_itens_atrasados,
       ROUND(AVG(CASE WHEN status_pedido = 'entregue' THEN nota_avaliacao END), 2) AS nota_media,
       ROUND(100.0 * AVG(CASE WHEN status_pedido IN ('cancelado', 'devolvido') THEN 1.0 ELSE 0.0 END), 2) AS pct_cancelado_devolvido
FROM pedidos;


-- ---------------------------------------------------------------------------
-- E) vw_atraso_chuva  ->  a chuva explica o atraso? (JOIN com chuva_diaria)
--    Colunas: faixa_chuva, itens, atraso_medio_dias, pct_atrasados
--    chuva_3d_mm = chuva do dia do pedido + os 2 dias seguintes, que e a janela
--    em que a coleta e a primeira perna do frete acontecem.
--    Faixas fechadas a esquerda e abertas a direita ([5, 20), [20, 40)), para
--    que 5 mm e 20 mm caiam em uma faixa so e nenhum item fique de fora.
--    O JOIN e INNER de proposito: as 23 cidades dos pedidos tem serie de chuva
--    completa (0 itens sem par, conferido), entao INNER e LEFT dao o mesmo
--    resultado aqui e o INNER deixa explicito que a faixa exige chuva conhecida.
--    ATENCAO na leitura: ver a view F do bonus antes de concluir causalidade.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_chuva AS
SELECT CASE
         WHEN c.chuva_3d_mm <  5  THEN '1) sem chuva (<5 mm)'
         WHEN c.chuva_3d_mm <  20 THEN '2) fraca (5-20)'
         WHEN c.chuva_3d_mm <  40 THEN '3) forte (20-40)'
         ELSE                          '4) muito forte (40+)'
       END                                                                       AS faixa_chuva,
       COUNT(*)                                                                  AS itens,
       ROUND(AVG(p.atraso_dias), 2)                                              AS atraso_medio_dias,
       ROUND(100.0 * AVG(CASE WHEN p.atraso_dias > 0 THEN 1.0 ELSE 0.0 END), 1)  AS pct_atrasados
FROM pedidos p
JOIN chuva_diaria c
  ON p.cidade = c.cidade
 AND p.data_pedido = c.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- F) vw_feriados  ->  feriado muda a operacao? (JOIN com feriados)
--    Colunas: tipo_dia, dias, pedidos, pedidos_por_dia, atraso_medio_dias
--    O LEFT JOIN usa SELECT DISTINCT dia: sem o DISTINCT, um dia com dois
--    feriados cadastrados duplicaria os pedidos daquele dia.
--    pedidos_por_dia normaliza a comparacao: 2025 tem ~14 feriados contra ~350
--    dias comuns, entao o total absoluto de pedidos nao diz nada.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_feriados AS
SELECT CASE WHEN f.dia IS NULL THEN 'dia comum' ELSE 'feriado' END       AS tipo_dia,
       COUNT(DISTINCT p.data_pedido)                                     AS dias,
       COUNT(DISTINCT p.pedido_id)                                       AS pedidos,
       ROUND(1.0 * COUNT(DISTINCT p.pedido_id)
                 / COUNT(DISTINCT p.data_pedido), 2)                     AS pedidos_por_dia,
       ROUND(AVG(p.atraso_dias), 2)                                      AS atraso_medio_dias
FROM pedidos p
LEFT JOIN (SELECT DISTINCT dia FROM feriados) f
  ON p.data_pedido = f.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1;


-- ---------------------------------------------------------------------------
-- BONUS) vw_atraso_chuva_regiao  ->  a pergunta e do grupo: o efeito da chuva
--    sobrevive quando se controla a regiao?
--    A view E compara chuva entre cidades, e Manaus e Belem chovem muito E
--    ficam longe dos centros de distribuicao. Essa view estratifica por regiao:
--    dentro de cada regiao, a mesma cidade enfrenta a mesma distancia, entao o
--    que varia entre as faixas de chuva e a chuva, nao a geografia.
--    Colunas: regiao, faixa_chuva, itens, atraso_medio_dias, pct_atrasados
--    Como ler: se o atraso subir com a chuva DENTRO de cada regiao, a chuva tem
--    efeito proprio; se ficar plano dentro das regioes e so diferir entre elas,
--    a chuva era um indicador da regiao, e nao a causa.
--    No dashboard esta view usa a regiao como dimensao de serie, lado a lado
--    com a view E, para mostrar as duas leituras na mesma tela.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_atraso_chuva_regiao AS
SELECT p.regiao,
       CASE
         WHEN c.chuva_3d_mm <  5  THEN '1) sem chuva (<5 mm)'
         WHEN c.chuva_3d_mm <  20 THEN '2) fraca (5-20)'
         WHEN c.chuva_3d_mm <  40 THEN '3) forte (20-40)'
         ELSE                          '4) muito forte (40+)'
       END                                                                       AS faixa_chuva,
       COUNT(*)                                                                  AS itens,
       ROUND(AVG(p.atraso_dias), 2)                                              AS atraso_medio_dias,
       ROUND(100.0 * AVG(CASE WHEN p.atraso_dias > 0 THEN 1.0 ELSE 0.0 END), 1)  AS pct_atrasados
FROM pedidos p
JOIN chuva_diaria c
  ON p.cidade = c.cidade
 AND p.data_pedido = c.dia
WHERE p.status_pedido = 'entregue'
GROUP BY 1, 2;
