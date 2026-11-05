# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

Matheus de Paula - 6325065
João Pedro Paulino - 6325175
Yuri Batista Sanches - 6325238

## Problema

É difícil saber qual operadora de plano de saúde dá mais problema, porque uma operadora grande sempre tem mais reclamações só por ter mais clientes. A ANS disponibiliza esses dados de graça, mas eles vêm espalhados em vários arquivos CSV grandes, o que dificulta a análise sem ferramentas de Big Data. Queremos descobrir quais operadoras têm mais reclamações em proporção ao número de clientes.

## Objetivos

Juntar os dados de beneficiários e de reclamações da ANS de pelo menos 12 meses.
Calcular as reclamações a cada 10 mil clientes e montar um ranking das operadoras.
Treinar um modelo simples para prever se as reclamações de uma operadora vão aumentar.
Mostrar os resultados em um dashboard.

## Dataset(s) e Fonte

Dados abertos da ANS (https://dadosabertos.ans.gov.br), baixados em CSV: beneficiários por operadora (um arquivo por estado por mês), reclamações registradas na ANS (NIP) e o cadastro de operadoras. Juntas, as bases devem passar de alguns GB. Se ficar pesado demais, vamos usar só alguns estados.

## Ferramentas de Big Data

S3: guardar os arquivos brutos e os tratados.
Spark / Spark SQL: ler, limpar, juntar e analisar os dados em paralelo.
Kafka: simular as reclamações chegando em tempo real.
Spark MLlib: treinar o modelo de previsão.
Superset: montar o dashboard final.

## Cronograma

Aula 11: escolha do tema e proposta.
Aula 12: baixar os dados, subir no S3 e limpar com Spark.
Aula 13: análises e modelo de Machine Learning.
Aula 14: dashboard e apresentação final.
