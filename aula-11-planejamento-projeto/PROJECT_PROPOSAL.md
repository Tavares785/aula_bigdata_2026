# Proposta de Projeto de Big Data

## Integrantes do Grupo

- <Nome: Henri da Silva Despezzi - 6325064>: Engenheiro de Dados (Kafka, ingestão e armazenamento no MongoDB)
- <Nome Pedro Otávio Ferreira Alves - 6325073>: Cientista de Dados (Spark, features e modelo de classificação)

O papel de Analista BI (dashboard) é dividido entre os dois integrantes.

## Problema

Fraudes em transações bancárias causam prejuízo financeiro direto e abalam a confiança dos clientes. Como a decisão de bloquear ou liberar uma transação precisa ser tomada em milissegundos, análises feitas apenas em lote, depois que a transação já ocorreu, chegam tarde demais. Além disso, fraudes são raras (menos de 1% das transações), o que dificulta a detecção e exige técnicas específicas para dados desbalanceados.

Este projeto investiga como detectar transações suspeitas em tempo real, em um cenário de fluxo contínuo de dados, usando ferramentas de Big Data.

## Objetivos

**Objetivo geral:** construir um pipeline de streaming que classifique transações bancárias como fraudulentas ou legítimas e exiba os resultados em um painel de monitoramento.

**Objetivos específicos:**

1. Ingerir o dataset via Kafka, simulando um fluxo contínuo de transações.
2. Processar o fluxo com Spark Structured Streaming e treinar um classificador com Spark MLlib.
3. Tratar o desbalanceamento das classes e avaliar o modelo com precision, recall e F1, com meta de recall acima de 80% na classe fraude.
4. Armazenar as transações classificadas no MongoDB.
5. Entregar um dashboard com indicadores como fraudes por hora, valor médio das transações fraudulentas e taxa de alertas.

**Perguntas de pesquisa:**

- Quais atributos mais diferenciam uma transação fraudulenta de uma legítima?
- Como lidar com o desbalanceamento das classes sem inflar a acurácia?
- Qual a latência entre a chegada de uma transação e a sua classificação?

## Dataset(s) e Fonte

- **Dataset:** PaySim, dataset sintético de transações de dinheiro móvel, disponível no Kaggle.
- **Volume aproximado:** cerca de 6 milhões de transações (aproximadamente 500 MB). Se necessário, o volume pode ser ampliado com dados sintéticos gerados por ferramentas como o Sparkov.
- **Formato original:** CSV.
- **Atributos principais:** tipo da transação, valor, saldos de origem e destino antes e depois da operação, e o rótulo `isFraud`.
- **Frequência de atualização:** dataset estático. A atualização contínua é simulada pelo envio das transações ao Kafka em fluxo.
- **Licença:** verificar e registrar a licença na página do dataset antes da entrega.

**Justificativa pelos 5 Vs:** Velocidade (fluxo contínuo de transações simulado via Kafka), Volume (milhões de registros) e Variedade (atributos numéricos e categóricos).

## Ferramentas de Big Data

- **Kafka:** recebe e entrega as transações como um fluxo contínuo, desacoplando a origem dos dados do processamento.
- **Spark (Structured Streaming e MLlib):** processa o fluxo em paralelo, cria as features e aplica o modelo de classificação em tempo real.
- **MongoDB (NoSQL):** armazena as transações classificadas em documentos flexíveis, com escrita rápida e consulta por qualquer campo.
- **Dashboard (Streamlit, Grafana ou MongoDB Charts):** apresenta os indicadores de fraude em tempo real.

**Arquitetura:** Dataset (PaySim) → Producer Kafka → tópico `transacoes` → Spark Structured Streaming (features + modelo MLlib) → MongoDB (coleção `transacoes_classificadas`) → Dashboard

## Cronograma

| Etapa | Responsável | Prazo |
|---|---|---|
| Escolha do tema, validação do dataset e da licença | Ambos | Semana 1 |
| Subir Kafka e producer simulando o fluxo | Eng. de Dados | Semana 2 |
| Análise exploratória e tratamento do desbalanceamento | Cientista de Dados | Semana 2 |
| Treino e avaliação do modelo (precision, recall, F1) | Cientista de Dados | Semana 3 |
| Streaming com Spark e gravação no MongoDB | Ambos | Semana 4 |
| Dashboard | Ambos | Semana 5 |
| Relatório e apresentação | Ambos | Semana 6 |