# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

Felipe Damasceno - 6325128

## Problema

O projeto visa resolver desafios enfrentados por lojas virtuais de petshop relacionados à personalização da experiência do cliente, otimização de estoque e previsão de demanda. Atualmente, muitas lojas online de produtos pet trabalham com catálogos extensos (rações, brinquedos, medicamentos, acessórios) e enfrentam dificuldades para:

- Recomendar produtos adequados ao perfil de cada pet e tutor
- Prever quais produtos terão maior demanda em diferentes períodos
- Identificar padrões de compra e comportamento dos clientes
- Reduzir rupturas de estoque de produtos essenciais
- Segmentar clientes para campanhas de marketing direcionadas

Este problema é relevante porque o mercado pet brasileiro movimenta bilhões anualmente e está em crescimento constante. A capacidade de personalizar ofertas e otimizar operações pode significar vantagem competitiva importante para e-commerces do setor.

## Objetivos

1. **Construir um sistema de recomendação de produtos** que sugira itens relevantes baseados no histórico de compras, tipo de pet, porte e necessidades específicas do cliente.

2. **Desenvolver modelo de previsão de demanda** para os 100 produtos mais vendidos, permitindo melhor planejamento de estoque e redução de custos com armazenagem.

3. **Implementar análise de sentimento** em avaliações de produtos para identificar problemas de qualidade e oportunidades de melhoria no catálogo.

4. **Criar segmentação de clientes** utilizando técnicas de clustering para identificar perfis distintos de compradores (ex: tutores de cães vs gatos, compradores de ração premium vs standard, etc.).

5. **Entregar dashboards interativos** que permitam aos gestores da loja visualizar métricas de vendas, comportamento de clientes e performance de produtos em tempo real.

**Resultados esperados:**
- Aumentar taxa de conversão em 15-20% através de recomendações personalizadas
- Reduzir rupturas de estoque em produtos críticos em 30%
- Identificar 5-7 segmentos distintos de clientes para campanhas direcionadas

## Dataset(s) e Fonte

**1. Dados transacionais da loja (principal)**
- **Fonte:** Dados sintéticos gerados simulando 2 anos de operação de uma loja virtual de petshop
- **Volume:** ~500.000 transações, 50.000 clientes únicos, 2.000 produtos
- **Conteúdo:** ID do pedido, cliente, produtos comprados, valores, timestamps, categoria de produto, informações do pet (tipo, porte, raça)

**2. Avaliações de produtos**
- **Fonte:** Dados sintéticos de reviews de clientes
- **Volume:** ~150.000 avaliações com texto, nota e data
- **Conteúdo:** Comentários dos clientes sobre produtos, ratings (1-5 estrelas)

**3. Dataset complementar de produtos pet**
- **Fonte:** Kaggle - "Pet Store Products Dataset" ou similar
- **Volume:** ~5.000-10.000 produtos com especificações
- **Conteúdo:** Categorias, preços de referência, marcas, especificações técnicas

**4. Dados de navegação (clickstream)**
- **Fonte:** Dados sintéticos simulando comportamento de navegação
- **Volume:** ~2 milhões de eventos de interação
- **Conteúdo:** Páginas visitadas, produtos visualizados, tempo de sessão, carrinho abandonado

**Justificativa do volume:** O dataset é grande o suficiente para aplicar técnicas de Big Data e pequeno o suficiente para ser processado em ambiente de desenvolvimento/aula.

## Ferramentas de Big Data

**1. Hadoop HDFS**
- **Uso:** Armazenamento distribuído dos datasets brutos (transações, avaliações, clickstream)
- **Justificativa:** Permite armazenar grandes volumes de dados históricos de forma distribuída e tolerante a falhas

**2. Apache Kafka**
- **Uso:** Ingestão de dados em tempo real simulando novos pedidos e eventos de navegação
- **Justificativa:** Simula um ambiente de streaming de dados onde novos eventos chegam continuamente à plataforma

**3. Apache Spark**
- **Uso:** Processamento dos dados para análises, feature engineering e treinamento de modelos
- **Justificativa:** Framework ideal para processar grandes volumes de dados e executar algoritmos de machine learning de forma distribuída

**4. MongoDB**
- **Uso:** Armazenar catálogo de produtos, perfis de clientes e resultados de recomendações
- **Justificativa:** Banco NoSQL flexível, adequado para dados semi-estruturados como catálogos de produtos com atributos variáveis

**5. Apache Hive**
- **Uso:** Queries SQL sobre dados históricos para análises exploratórias e geração de relatórios
- **Justificativa:** Permite análises usando SQL sobre dados no HDFS, facilitando queries analíticas complexas

**6. Apache Zeppelin**
- **Uso:** Notebooks interativos para análises exploratórias, visualizações e documentação do projeto
- **Justificativa:** Interface amigável para executar Spark jobs, criar visualizações e documentar descobertas

**7. Spark MLlib**
- **Uso:** Implementação dos modelos de recomendação (Collaborative Filtering), clustering (K-means) e previsão de demanda (regressão/séries temporais)
- **Justificativa:** Biblioteca escalável de machine learning integrada ao Spark

**8. Spark NLP ou bibliotecas de processamento de texto**
- **Uso:** Análise de sentimento nas avaliações dos produtos
- **Justificativa:** Extrair insights qualitativos dos comentários dos clientes sobre produtos

## Cronograma

**Semana 1-2: Preparação e Coleta de Dados**
- Configuração do ambiente (Hadoop, Kafka, Spark, MongoDB)
- Geração/coleta dos datasets sintéticos e de fontes públicas
- Ingestão inicial dos dados no HDFS
- Setup do MongoDB com schema de produtos e clientes

**Semana 3-4: Exploração e Limpeza de Dados**
- Análise exploratória dos dados usando Zeppelin
- Limpeza e tratamento de valores ausentes/inconsistentes
- Queries com Hive para entender distribuições e padrões
- Feature engineering inicial

**Semana 5-6: Modelagem - Sistema de Recomendação**
- Implementação de Collaborative Filtering com Spark MLlib
- Treinamento e validação do modelo de recomendação
- Ajuste de hiperparâmetros
- Geração de recomendações e armazenamento no MongoDB

**Semana 7-8: Modelagem - Previsão de Demanda**
- Análise de séries temporais de vendas
- Implementação de modelos preditivos (Regressão, ARIMA, Prophet)
- Validação com dados de teste (últimos 3 meses)
- Comparação de performance entre modelos

**Semana 9-10: Análise de Sentimento e Clustering**
- Processamento de texto das avaliações com NLP
- Análise de sentimento e extração de insights
- Clustering de clientes (K-means)
- Interpretação e caracterização dos segmentos

**Semana 11-12: Visualização e Documentação**
- Criação de dashboards no Zeppelin
- Configuração do pipeline Kafka para streaming simulado
- Documentação completa do projeto
- Preparação da apresentação final

**Entrega Final: Semana 12**
