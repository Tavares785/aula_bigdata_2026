## Integrantes do Grupo

Leonardo Rafael Contini Costa - 6325054

## Problema

A Amazon precisava registrar cada clique, histórico de busca e transação de milhões de clientes simultaneamente para alimentar seus primeiros sistemas de recomendação. Os bancos de dados tradicionais travavam com a concorrência massiva de gravações simultâneas (writes), o que forçou empresas de e-commerce a repensarem como armazenar logs e eventos sem estrutura pré-definida.

## Objetivos

Criar o primeiro sistema de recomendações de produtos da Amazon

## Dataset(s) e Fonte

Origem dos Dados (Fontes Primárias):

Logs de Servidores Web (Clickstream): Arquivos de texto brutos gerados pelos servidores Apache/IIS que registravam cada clique, visualização de página, tempo de permanência e rota de navegação dos usuários.

Transações de Clientes: Histórico completo de compras, dados de carrinho de compras, endereços e transações de cartão de crédito.

Histórico de Buscas: Termos digitados na barra de pesquisa do site.

Avaliações e Perfis: Notas e comentários deixados pelos próprios clientes nos produtos.

Volume Aproximado:

Embora pareça pequeno para os padrões atuais, na época era considerado Massivo (Gigabytes altos caminhando para Terabytes) — um volume impensável para a capacidade de processamento dos bancos de dados relacionais tradicionais da época em uma única máquina.

## Ferramentas de Big Data

Ferramentas Escolhidas e Justificativas para o Cenário da Amazon
1. Apache Kafka (Ingestão de Dados em Tempo Real)

Por que faz sentido: No cenário da Amazon, milhões de usuários geravam cliques e buscas simultaneamente. O Kafka atua como um sistema de mensageria altamente escalável capaz de absorver essa enxurrada massiva de eventos de clique (clickstream) sem travar, desacoplando a captura dos dados do processamento posterior.

2. Hadoop (HDFS - Hadoop Distributed File System) (Armazenamento Distribuído)

Por que faz sentido: Os dados de logs e histórico de navegação vinham em formato bruto (texto não estruturado) e em volume massivo (terabytes). O HDFS resolve o problema do alto custo de hardware ao permitir armazenar esses arquivos distribuídos em milhares de computadores comuns e baratos.

3. Apache Spark (Processamento Distribuído de Alta Performance)

Por que faz sentido: Para calcular as recomendações de produtos (filtragem colaborativa), a Amazon precisava cruzar o histórico de milhões de usuários. O Spark substitui o antigo MapReduce com processamento em memória, acelerando drasticamente o cruzamento de dados em larga escala.

4. Apache Cassandra ou HBase (NoSQL - Banco de Dados de Alta Concorrência)

Por que faz sentido: Os bancos relacionais tradicionais travavam com bloqueios (locks) devido à concorrência massiva de gravações (writes). Bancos NoSQL orientados a colunas/chaves oferecem alta disponibilidade e escalabilidade horizontal linear, permitindo registrar compras e cliques em tempo real sem gargalos.

5. Apache Hive (Data Warehouse / Consultas SQL em Big Data)

Por que faz sentido: Os engenheiros e analistas precisavam extrair insights dos logs brutos armazenados no Hadoop, mas programar em Java (MapReduce puro) era inviável. O Hive permitia rodar consultas estruturadas semelhantes ao SQL sobre dados não estruturados de forma simples.

6. Apache Zeppelin ou Superset (Visualização e Análise Interativa)

Por que faz sentido: Para que as equipes de negócios da Amazon pudessem monitorar o comportamento de consumo, tendências de busca e o impacto dos algoritmos de recomendação através de dashboards visuais interativos.

7. Spark MLlib e NLP (Machine Learning e Processamento de Linguagem Natural)

Por que faz sentido: Essenciais para construir e treinar o motor de recomendação preditiva da Amazon (analisando padrões de compra) e para processar os termos de busca digitados pelos clientes e as avaliações (reviews) dos produtos.

## Cronograma

Fase 1: Ingestão e Armazenamento Base (Semanas 1 a 4)
Objetivo: Estabelecer a infraestrutura fundamental para capturar o fluxo massivo de dados de cliques (clickstream) e armazená-los sem travar.

Etapas:

Configuração do cluster Hadoop (HDFS) para armazenamento distribuído de baixo custo de logs e arquivos brutos.

Implementação do Apache Kafka para atuar como o barramento central de mensageria em tempo real, absorvendo picos de cliques e buscas dos usuários.

Ferramentas envolvidas: Hadoop (HDFS), Apache Kafka.

Fase 2: Processamento Distribuído e Persistência de Alta Concorrência (Semanas 5 a 8)
Objetivo: Substituir os bancos relacionais tradicionais por uma tecnologia NoSQL capaz de suportar milhões de gravações simultâneas de carrinhos e transações, e preparar o motor de processamento.

Etapas:

Modelagem e implantação do Apache Cassandra (ou HBase) para garantir alta disponibilidade e escrita ultrarrápida sem bloqueios de tabela (locks).

Configuração do Apache Spark para processar os dados em memória e transformar os logs brutos em dados limpos e estruturados.

Ferramentas envolvidas: Apache Cassandra/HBase, Apache Spark.

Fase 3: Inteligência, Consultas Analíticas e Machine Learning (Semanas 9 a 12)
Objetivo: Criar a camada de inteligência do e-commerce (o motor de recomendação) e permitir que analistas consultem o Big Data usando SQL.

Etapas:

Desenvolvimento e treinamento dos algoritmos de recomendação (Filtragem Colaborativa) utilizando Spark MLlib e técnicas de NLP para processar avaliações de produtos e termos de busca.

Configuração do Apache Hive para mapear os dados do HDFS e permitir consultas analíticas rápidas via linguagem SQL.

Ferramentas envolvidas: Spark MLlib, NLP, Apache Hive.

Fase 4: Visualização, Dashboards e Validação Final (Semanas 13 a 16)
Objetivo: Entregar painéis visuais para a equipe de negócios monitorar o comportamento dos clientes e validar o sistema em ambiente de testes/produção.

Etapas:

Criação de dashboards interativos no Apache Zeppelin (ou Superset) para exibir métricas de conversão, eficácia das recomendações e fluxo de tráfego.

Testes de carga simulando o tráfego de milhões de usuários e ajustes finais de performance.

Ferramentas envolvidas: Apache Zeppelin / Superset.