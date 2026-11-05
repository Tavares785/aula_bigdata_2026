# Proposta de Projeto de Big Data

## Integrantes do Grupo

6325095 - Caique Pereira de Souza  
6325213 - Daniel Alves Pinheiro  
6325028 - Denise Maider Batista De Macedo  
6325066 - Maximus Ponciano  

## Problema

**Análise de acidentes de trânsito nas rodovias brasileiras.**

O Brasil registra dezenas de milhares de acidentes com vítimas por ano apenas
nas rodovias federais, com alto custo humano, social e econômico. Os órgãos
de trânsito publicam registros detalhados desses acidentes (local, data,
hora, causa, tipo, condições climáticas, gravidade), mas o volume e a
dispersão desses dados dificultam uma análise manual.

Com uma grande quantidade de dados é possível identificar padrões que
não aparecem em amostras pequenas: trechos de rodovia com concentração
anormal de acidentes (pontos críticos), horários e dias da semana de maior
risco, causas mais frequentes e condições que aumentam a gravidade. Esse
tipo de análise é relevante porque apoia decisões de fiscalização,
sinalização, campanhas educativas e planejamento de infraestrutura,
contribuindo diretamente para a redução de mortes no trânsito.

## Objetivos

1. **Construir um pipeline de ingestão e processamento** capaz de
   consolidar os registros de acidentes de múltiplos anos em um único
   dataset limpo e padronizado (tratamento de valores nulos, encoding,
   formatos de data/hora, coordenadas inválidas).
2. **Identificar os pontos críticos (hotspots)**: ranquear os 20 trechos
   (rodovia + km) com maior número de acidentes e maior número de vítimas
   fatais, no Brasil e no estado de São Paulo.
3. **Caracterizar o perfil temporal dos acidentes**: distribuição por hora
   do dia, dia da semana, mês e feriados, identificando as janelas de maior
   risco.
4. **Analisar causas e fatores agravantes**: relação entre tipo de
   acidente, causa provável, condição meteorológica, tipo de pista e
   gravidade (ilesos, feridos leves, feridos graves, mortos).
5. **Treinar um modelo de classificação** (com MLlib) para prever se um
   acidente terá vítima grave ou fatal a partir de suas características,
   com meta de atingir pelo menos 70% de acurácia balanceada / F1 na
   classe de interesse.
6. **Entregar um dashboard interativo** com mapas de calor, séries
   temporais e rankings, permitindo filtrar por estado, rodovia, ano e
   gravidade.

Entregas finais: código do pipeline (repositório), dataset tratado,
notebooks de análise, modelo treinado com métricas, dashboard e relatório
técnico com os principais achados.

## Dataset(s) e Fonte

**Dataset principal — Dados Abertos de Acidentes da PRF (Polícia
Rodoviária Federal).**
Fonte: portal de dados abertos do Governo Federal (gov.br / PRF).
Conjunto "Acidentes por ocorrência" e "Acidentes por pessoa", publicados
anualmente em CSV desde 2007. Cada registro contém data, hora, UF, BR,
km, município, causa, tipo de acidente, classificação (com/sem vítimas),
fase do dia, condição meteorológica, tipo e traçado da pista, uso do solo,
latitude/longitude (a partir de 2017), além dos totais de pessoas, feridos
e mortos.
Volume aproximado: cerca de 60–70 mil ocorrências por ano no arquivo por
ocorrência e 150–200 mil linhas por ano no arquivo por pessoa. Usando o
período 2017–2025, o conjunto totaliza algo entre 1,5 e 2 milhões de
linhas e aproximadamente 1 GB em CSV.

**Dataset complementar — Infosiga SP.**
Fonte: Governo do Estado de São Paulo (Detran-SP / Infosiga), dados
abertos de sinistros de trânsito em vias estaduais e municipais de SP,
com geolocalização. Permite aprofundar a análise na região do grupo e
comparar rodovias federais e vias urbanas. Volume: centenas de milhares
de registros desde 2015.

**Dados auxiliares (opcional):** calendário de feriados nacionais e
estaduais (para o eixo temporal) e malha das rodovias (shapefiles do
DNIT) para a visualização em mapa.

Todos os dados são públicos e anonimizados, sem restrição de uso.

## Ferramentas de Big Data

- **Hadoop (HDFS):** armazenamento distribuído dos arquivos CSV brutos de
  todos os anos e das camadas intermediárias (raw → tratado → agregado).
  Faz sentido porque o volume cresce a cada ano incluído e queremos um
  repositório único, tolerante a falhas, acessível pelas demais
  ferramentas.
- **Apache Spark (PySpark):** motor principal de processamento. Será usado
  para a limpeza e padronização dos dados (os arquivos da PRF mudam de
  schema e encoding entre anos), para as agregações por trecho/hora/causa
  e para os joins com os dados complementares. Escolhido pela capacidade
  de processar os milhões de linhas em memória de forma distribuída e por
  integrar nativamente com HDFS, Hive e MLlib.
- **Hive:** camada SQL sobre os dados tratados no HDFS, com tabelas
  particionadas por ano e UF. Permite que consultas analíticas (ranking
  de trechos, totais por período) sejam escritas em SQL e reaproveitadas
  pelo dashboard.
- **Spark MLlib:** treinamento do modelo de classificação de gravidade
  (ex.: Random Forest ou Gradient-Boosted Trees), com pipeline de
  feature engineering (StringIndexer, OneHotEncoder, VectorAssembler),
  validação cruzada e avaliação de métricas.
- **Apache Superset (ou Zeppelin):** construção do dashboard interativo
  conectado ao Hive/Spark, com mapas de calor dos hotspots, gráficos de
  distribuição temporal e filtros por estado, rodovia e gravidade.
  Zeppelin será usado como ambiente de notebooks para a análise
  exploratória.
- **Kafka (extensão, se houver tempo):** simular a chegada de ocorrências
  em tempo quase real, consumindo um stream com Spark Structured
  Streaming para atualizar contadores de acidentes por trecho — exercício
  que mostra como o mesmo pipeline funcionaria com dados ao vivo.
- **MongoDB (opcional):** armazenamento dos resultados agregados em
  formato de documento (um documento por trecho crítico, com histórico e
  estatísticas), facilitando o consumo por uma aplicação ou API.

## Cronograma

| Etapa | Atividades | Prazo |
|---|---|---|
| 1. Levantamento e coleta | Download dos arquivos da PRF (2017–2025) e Infosiga SP; análise inicial de schema, encoding e qualidade; definição do escopo final. | 05/11 – 11/11/2026 |
| 2. Infraestrutura | Configuração do ambiente (HDFS, Spark, Hive, Superset); carga dos dados brutos no HDFS. | 12/11 – 15/11/2026 |
| 3. Limpeza e padronização | Pipeline PySpark de tratamento; unificação dos anos; criação das tabelas Hive particionadas. | 16/11 – 22/11/2026 |
| 4. Análise exploratória | Hotspots, perfil temporal, causas e gravidade; notebooks no Zeppelin; validação dos primeiros achados. | 23/11 – 29/11/2026 |
| 5. Modelagem | Feature engineering, treinamento e avaliação do modelo de gravidade com MLlib. | 30/11 – 06/12/2026 |
| 6. Dashboard | Construção das visualizações no Superset; integração com as tabelas Hive. | 07/12 – 11/12/2026 |
| 7. Relatório e apresentação | Redação do relatório técnico, organização do repositório e ensaio da apresentação. | 12/12 – 16/12/2026 |
| Entrega final | Apresentação e entrega de todos os artefatos. | 17/12/2026 (ajustar à data do curso) |

Responsabilidades: cada integrante lidera uma frente (coleta/infra,
pipeline Spark/Hive, modelagem MLlib, dashboard/relatório), com revisão
cruzada semanal.