# Proposta de Projeto de Big Data

## Integrantes do Grupo

- Fernanda Novais (RA 4025109)

## Problema

Em um marketplace de e-commerce, atrasos na entrega e problemas com produtos
viram avaliações negativas, e cada avaliação negativa aumenta a chance de o
cliente não comprar de novo. Hoje esse sinal só é percebido dias depois, quando
alguém olha um relatório. O projeto investiga **quais fatores operacionais
(prazo de entrega, frete, categoria, região) levam a avaliações negativas** e
monta um pipeline que **detecta reclamações assim que chegam**, para que a
equipe de atendimento aja antes de perder o cliente.

O problema é relevante porque reputação é um dos principais fatores de
conversão no varejo online, e o volume de pedidos e textos de avaliação torna
inviável analisar tudo manualmente.

## Objetivos

1. **Diagnóstico:** medir a relação entre atraso na entrega (data real vs.
   data estimada) e a nota da avaliação, por estado e por categoria de produto.
2. **Classificação de sentimento:** classificar o texto das avaliações em
   positivo/negativo com NLP (tokenização, stopwords, stemming) e um modelo
   do Spark MLlib, com meta de **acurácia ≥ 80%** usando a nota (1–5) como
   rótulo de referência.
3. **Predição de avaliação negativa:** treinar um classificador (Logistic
   Regression no MLlib) que preveja, a partir de dados do pedido, se a
   avaliação será negativa (nota ≤ 2), com meta de **AUC-ROC ≥ 0,75**.
4. **Detecção em tempo (quase) real:** simular a chegada de avaliações via
   Kafka e sinalizar reclamações em até **1 minuto** com Spark Structured
   Streaming.
5. **Entrega final:** um dashboard com as métricas por região, categoria e
   período, mais um relatório com as respostas às perguntas acima.

## Dataset(s) e Fonte

- **Brazilian E-Commerce Public Dataset by Olist** (Kaggle):
  aproximadamente 100 mil pedidos reais (2016–2018), em 9 arquivos CSV
  relacionados (pedidos, itens, clientes, vendedores, produtos, pagamentos,
  geolocalização e avaliações). Cerca de 100 mil avaliações, boa parte com
  comentário em português. Volume aproximado de 120 MB em CSV.
- **Dados sintéticos de streaming:** um produtor Python vai reenviar as
  avaliações para o Kafka em ordem cronológica e acelerada, simulando um fluxo
  contínuo. Se precisar testar volume maior, o produtor pode replicar os
  registros com ruído para chegar a milhões de eventos.

## Ferramentas de Big Data

| Ferramenta | Uso no projeto | Por que faz sentido |
|---|---|---|
| **HDFS / S3** (Hadoop) | Armazenar os CSVs brutos e as saídas em Parquet (camada bronze/prata/ouro do data lake) | Armazenamento distribuído e barato, separado do processamento |
| **Apache Kafka** | Tópico `avaliacoes` recebendo os eventos simulados | Desacopla quem produz os eventos de quem processa e guarda o fluxo para reprocessar |
| **Spark Structured Streaming** | Consumir o Kafka, classificar o sentimento e sinalizar reclamações em janelas de 1 minuto | Mesma API do Spark batch, com processamento incremental |
| **Spark SQL / Hive** | Modelo dimensional (fato pedidos; dimensões cliente, produto, vendedor, tempo) e consultas analíticas (`GROUP BY`, `HAVING`, top-N) | SQL conhecido sobre dados distribuídos, como no Data Warehouse da aula 09 |
| **MongoDB** | Guardar avaliações enriquecidas (texto, sentimento, alertas) como documentos para a equipe de atendimento consultar | Esquema flexível para o texto e consultas rápidas por pedido ou cliente |
| **Spark MLlib** | `VectorAssembler` + `LogisticRegression` para prever avaliação negativa; avaliação com accuracy e AUC-ROC | Treino distribuído, no mesmo pipeline da aula 07 |
| **NLP** | Tokenização, remoção de stopwords em português, stemming e score por léxico, depois TF-IDF como features para o MLlib | O texto das avaliações é a principal fonte do sentimento |
| **Apache Superset** | Dashboard com nota média, % de negativas, atraso médio por estado e categoria e média móvel diária | Ferramenta de BI aberta que conecta direto às tabelas do warehouse |
| **Docker / docker-compose** | Subir Kafka, Spark e MongoDB localmente de forma reproduzível | Mesmo ambiente para todos e para a demonstração |

## Cronograma

| Semana | Período | Etapa | Entregável |
|---|---|---|---|
| 1 | 11/11 – 17/11/2026 | Definição do problema, download e exploração dos dados | Esta proposta + notebook de análise exploratória |
| 2 | 18/11 – 24/11/2026 | Ingestão no data lake (HDFS/S3) e limpeza com Spark; modelo dimensional no Spark SQL/Hive | Tabelas Parquet + consultas de diagnóstico (objetivo 1) |
| 3 | 25/11 – 01/12/2026 | Pipeline de NLP e modelos do MLlib (sentimento e avaliação negativa) | Métricas de accuracy e AUC-ROC (objetivos 2 e 3) |
| 4 | 02/12 – 08/12/2026 | Produtor Kafka + Spark Structured Streaming + gravação dos alertas no MongoDB | Pipeline de streaming funcionando (objetivo 4) |
| 5 | 09/12 – 15/12/2026 | Dashboard no Superset, testes de ponta a ponta e relatório | Dashboard + relatório final (objetivo 5) |
| 6 | 16/12 – 18/12/2026 | Ajustes finais e apresentação | Apresentação do projeto |
