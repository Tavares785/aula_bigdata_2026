# Proposta de Projeto de Big Data

## Integrantes do Grupo

Emar Cristian Silva Teruo Ito - RA 6325192.

## Problema

Empresas que processam grandes quantidades de pedidos precisam analisar faturamento, comportamento de vendas e atrasos nas entregas. A falta de indicadores consolidados dificulta a identificacao de problemas operacionais e a tomada de decisoes.

Este projeto investigara padroes de vendas e fatores associados a atrasos em pedidos ficticios.

## Objetivos

- Processar aproximadamente 100.000 registros de pedidos.
- Calcular faturamento total, quantidade de pedidos e ticket medio.
- Identificar o percentual de entregas atrasadas.
- Analisar faturamento por categoria, regiao e periodo.
- Construir e avaliar um modelo de classificacao de risco de atraso.
- Apresentar indicadores e graficos para apoiar decisoes.

## Dataset(s) e Fonte

Sera utilizado um dataset sintetico com aproximadamente 100.000 pedidos, gerado por um script Python com semente aleatoria fixa para garantir reproducibilidade.

A base incluira identificador, data, categoria, regiao, quantidade, valor unitario, valor total, prazo previsto, tempo de entrega e indicador de atraso.

Os registros serao ficticios, sem informacoes pessoais de clientes reais. A geracao dos dados sera documentada na aula 12.

## Ferramentas de Big Data

- Python: geracao e organizacao dos dados.
- Apache Spark e PySpark: ingestao, limpeza e processamento.
- Spark SQL: consultas e agregacoes de vendas.
- Spark MLlib: modelo de classificacao de risco de atraso.
- Matplotlib: visualizacao de resultados e indicadores.

A execucao sera local, permitindo reproducibilidade sem servicos pagos ou infraestrutura AWS.

## Cronograma

- Aula 11: definir escopo, dados, objetivos e ferramentas.
- Aula 12: gerar o dataset e implementar ingestao e pre-processamento.
- Aula 13: realizar analises e treinar e avaliar o modelo.
- Aula 14: gerar graficos, interpretar indicadores e concluir o projeto.
