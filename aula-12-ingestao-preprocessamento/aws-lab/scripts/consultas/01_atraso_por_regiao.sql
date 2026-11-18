SELECT regiao,
       SUM(itens) AS itens,
       ROUND(SUM(pct_itens_atrasados * itens) / SUM(itens), 2) AS pct_itens_atrasados,
       ROUND(SUM(atraso_medio_dias * itens) / SUM(itens), 2) AS atraso_medio_dias
FROM atraso_estado_mes
GROUP BY regiao
ORDER BY pct_itens_atrasados DESC;
