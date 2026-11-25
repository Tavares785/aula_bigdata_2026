# Proposta de Projeto de Big Data

## Integrantes do Grupo

- Carina Dalpino
- Luiza

## Problema

Fraudes em transações financeiras causam prejuízos bilionários a bancos e
clientes todos os anos. O desafio é que o volume de transações é muito
alto e a fraude é um evento raro (menos de 1% dos casos), o que torna
inviável a análise manual e exige processamento contínuo. Quanto mais
tarde a fraude é detectada, maior o dano: a transação já foi concluída e
o valor dificilmente é recuperado.

Este projeto investiga como monitorar um fluxo de transações em tempo
real e sinalizar operações suspeitas assim que elas chegam, usando uma
arquitetura de Big Data capaz de escalar com o volume de dados.

## Objetivos

1. Construir um pipeline de streaming que receba transações em um tópico
   Kafka e as processe com Spark Streaming.
2. Aplicar regras e/ou um modelo de classificação para marcar cada
   transação como suspeita ou normal durante o processamento.
3. Armazenar as transações processadas e os alertas de fraude em um
   banco NoSQL (MongoDB), permitindo consulta posterior.
4. Avaliar a detecção com métricas adequadas a dados desbalanceados
   (precisão, recall e F1 da classe fraude), e não apenas acurácia.
5. Medir a latência entre a chegada da transação e a emissão do alerta,
   com meta de processar cada micro-lote em poucos segundos.
6. Entregar ao final um painel simples com o volume de transações e os
   alertas gerados.

## Dataset(s) e Fonte

**Fonte:** dataset "Credit Card Fraud Detection", disponível no Kaggle
(https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud), com
transações reais de cartões europeus, anonimizadas.

**Volume:** cerca de 285 mil transações (aproximadamente 150 MB em CSV),
com 30 atributos numéricos, entre eles o valor (`Amount`) e o tempo
(`Time`), mais a coluna de rótulo (`Class`: 1 = fraude, 0 = normal).

**Característica principal:** a base é fortemente desbalanceada. Apenas
492 transações (cerca de 0,17%) são fraudes. Por isso a avaliação usará
precisão, recall e F1 da classe fraude.

**Simulação de streaming:** as transações serão publicadas em um tópico
Kafka em ordem, em velocidade configurável, para simular um fluxo
contínuo de eventos.

**Teste de carga:** como a base original é pequena para Big Data, o
conjunto será replicado para gerar milhões de eventos e medir a latência
e a vazão do pipeline em volume maior.

**Limitações:** os dados são de 2013 e de portadores europeus, e as
variáveis foram anonimizadas, o que limita a interpretação de negócio
de cada atributo.

## Ferramentas de Big Data

- **Apache Kafka:** recebe as transações como um fluxo contínuo de
  eventos. Desacopla quem produz as transações de quem as processa e
  permite reprocessar o histórico, o que é útil para testes de carga.
- **Spark Streaming:** consome o tópico Kafka em micro-lotes, aplica o
  modelo de classificação a cada transação e escala com o volume de
  eventos, atendendo ao requisito de baixa latência.
- **Spark MLlib:** treina o classificador de fraude (por exemplo Random
  Forest ou regressão logística com pesos de classe, para lidar com o
  desbalanceamento) no mesmo ecossistema do processamento, sem mover os
  dados para outra ferramenta.
- **MongoDB:** armazena as transações processadas e os alertas de
  fraude. O modelo de documentos comporta bem eventos semiestruturados e
  permite consultar os alertas rapidamente.
- **Apache Superset ou Zeppelin:** painel com o volume de transações e
  os alertas gerados, para a visualização final do projeto.
- **Amazon S3:** guarda o CSV original e os resultados do processamento,
  funcionando como data lake do projeto.

## Cronograma

Os prazos de entrega seguem o calendário das aulas definido pelo
professor. Cada etapa corresponde a uma aula do projeto.

1. **Definição e planejamento (Aula 11):** escolha do tema, do dataset e
   das ferramentas, e redação desta proposta.
2. **Ingestão e pré-processamento (Aula 12):** baixar o dataset e
   guardá-lo no S3, criar o produtor Kafka que publica as transações em
   velocidade configurável, ler o tópico com Spark Streaming e fazer a
   limpeza e a preparação dos atributos. Gerar também a base replicada
   para o teste de carga.
3. **Análise e construção do modelo (Aula 13):** treinar o classificador
   com Spark MLlib (com pesos de classe), aplicá-lo ao fluxo, gravar
   transações e alertas no MongoDB e calcular precisão, recall e F1 da
   classe fraude, além da latência por micro-lote.
4. **Visualização e conclusão (Aula 14):** montar o painel no Superset
   ou Zeppelin com o volume de transações e os alertas, e apresentar os
   resultados, as limitações e as lições aprendidas.