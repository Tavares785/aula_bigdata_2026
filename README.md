# 🐘 Ecossistema Big Data e Engenharia de Dados

Bem-vindos ao repositório oficial da disciplina de Big Data! Neste semestre, vamos mergulhar no universo do processamento de dados em larga escala. Vocês deixarão de ser apenas consumidores de informação para se tornarem os engenheiros que constroem as fundações tecnológicas das maiores empresas do mundo.

Abaixo, apresentamos a trilha de aprendizagem dividida em módulos estratégicos.

---

## 📚 Módulos e Roteiro de Estudos

### 🌐 Módulo 1: Fundamentos e Infraestrutura Base (Aulas 1 e 2)
Vamos entender a origem da explosão de dados e as tecnologias fundamentais que permitem armazenar informações além do limite de um único computador.

**O que vamos dominar:**
* O conceito central do Big Data e os 5 Vs (Volume, Velocidade, Variedade, Veracidade, Valor) aplicados em setores reais como saúde e finanças.
* Os desafios técnicos e éticos (privacidade e segurança) no manuseio de dados globais.
* Introdução ao ecossistema **Apache Hadoop** e seus pilares: Sistema de Arquivos Distribuído (HDFS), processamento paralelo (MapReduce) e gerenciamento de recursos (YARN).
* *Prática:* Configuração e execução de tarefas MapReduce em clusters.

**🔍 Para pesquisar antes das aulas:**
1. O que é um "Sistema de Arquivos Distribuído" e por que ele é diferente do disco rígido (HD) comum do seu computador?
2. Em termos simples, qual é a diferença entre *Scale-Up* (escala vertical) e *Scale-Out* (escala horizontal) em infraestrutura de TI?

---

### ⚡ Módulo 2: Processamento em Tempo Real e Bancos NoSQL (Aulas 3 e 4)
Nem todo dado pode esperar. Aprenderemos a processar informações no exato momento em que elas nascem e a armazená-las em bancos ultra rápidos.

**O que vamos dominar:**
* Mensageria e streaming em tempo real com **Apache Kafka** (tópicos, partições, produtores e consumidores) e **Spark Streaming**.
* Quebra do paradigma relacional com bancos **NoSQL**: arquiteturas de Chave-Valor, Coluna, Documento e Grafo.
* Imersão e comandos básicos em ferramentas de mercado: MongoDB (documentos), Apache Cassandra e HBase (colunas).
* *Prática:* Implementar aplicações de streaming e consultar múltiplos bancos NoSQL.

**🔍 Para pesquisar antes das aulas:**
1. Imagine o fluxo de dados da Uber ou do PIX. Como o Apache Kafka ajuda esses sistemas a não caírem durante picos de uso?
2. Qual a diferença fundamental entre um banco de dados Relacional (SQL) e um banco Baseado em Documentos (como o MongoDB)?

---

### 🧠 Módulo 3: O Poder do Apache Spark e Inteligência Analítica (Aulas 5 a 8)
Nesta fase, dominaremos a ferramenta líder de processamento em memória e aplicaremos Inteligência Artificial em volumes massivos de dados.

**O que vamos dominar:**
* Arquitetura do **Apache Spark** (Driver e Executors) e a abstração de dados em RDDs e DataFrames.
* Processamento e análise de dados estruturados utilizando **Spark SQL**.
* Paralelização de modelos de Machine Learning (Classificação, Clustering, Regressão) utilizando **Spark MLlib**.
* Aplicação de Processamento de Linguagem Natural (NLP) em larga escala (análise de sentimentos e tópicos) com Spark NLP.
* *Prática:* Desenvolvimento de análises em larga escala, treinamento de modelos de ML e análise de sentimentos em tweets.

**🔍 Para pesquisar antes das aulas:**
1. Por que o Apache Spark é considerado, em média, 100 vezes mais rápido que o tradicional Hadoop MapReduce?
2. O que é Tokenização e Lematização dentro do Processamento de Linguagem Natural (NLP)?

---

### 🗄️ Módulo 4: Arquitetura de Repositórios e Visualização (Aulas 9 e 10)
Como empresas organizam seus dados brutos e como eles são entregues de forma visual para os diretores tomarem decisões.

**O que vamos dominar:**
* As diferenças arquiteturais e casos de uso entre **Data Warehousing** (dados modelados) e **Data Lakes** (dados brutos).
* Motores de consulta SQL sobre Hadoop: Apache Hive e Apache Impala.
* Desafios visuais em Big Data e criação de dashboards interativos usando Apache Zeppelin e Apache Superset.
* *Prática:* Executar consultas SQL sobre HDFS e conectar plataformas de visualização para gerar insights.

**🔍 Para pesquisar antes das aulas:**
1. Qual a diferença entre um Data Warehouse e um Data Lake? (Dica: pense em água engarrafada vs. um lago natural).
2. O que é uma ferramenta de *Business Intelligence* (BI)? 

---

### 🚀 Módulo 5: Projeto Final de Big Data (Aulas 11 a 14)
A consolidação do conhecimento. Vocês atuarão como Engenheiros e Cientistas de Dados desenvolvendo um projeto completo do zero.

**O que vamos dominar:**
* Aula 11: Definição de escopo, escolha da base de dados e planejamento do projeto.
* Aula 12: Ingestão de grandes bases e pré-processamento de dados utilizando as ferramentas aprendidas (S3, Spark, Kafka).
* Aula 13: Aplicação de análises robustas e construção de modelos de Machine Learning ou NLP em escala.
* Aula 14: Criação de dashboards significativos e apresentação corporativa dos insights e lições aprendidas do projeto.

**🔍 Para pesquisar antes das aulas:**
1. Encontrem conjuntos de dados abertos (*datasets*) interessantes no site Kaggle (kaggle.com) ou no Portal de Dados Abertos do Governo Brasileiro. O que vocês gostariam de analisar?

---

---

## 🐳 Como fazer os labs (TF - Trabalho de Casa)

Cada aula técnica (2 a 10) tem um **lab prático** com correção automática.
Cada lab vem com um **ambiente Docker** completo — você **não precisa
instalar Python, Java nem Spark** na sua máquina.

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado
- [Git](https://git-scm.com/) instalado
- Conta no GitHub

### Fluxo de entrega

1. **Fork** este repositório (botão "Fork" no GitHub)
2. **Clone** o seu fork:
   ```bash
   git clone https://github.com/SEU-USUARIO/labs-big-data.git
   cd labs-big-data
   ```
3. **Crie uma branch** para o lab:
   ```bash
   git checkout -b aula-XX-SEURA
   ```
4. **Complete os TODOs** nos arquivos `src/` da aula
5. **Teste localmente com Docker**:
   ```bash
   cd aula-XX-nome
   docker build -t lab-aula-XX .
   docker run --rm lab-aula-XX
   ```
6. **Commit e push**:
   ```bash
   git add .
   git commit -m "Aula XX: implementação do lab"
   git push origin aula-XX-SEURA
   ```
7. **Abra uma Pull Request** para a branch `main` do repositório original
8. O **GitHub Actions** roda automaticamente a correção dentro do mesmo
   container Docker — aguarde ✅ ou ❌ na PR

> **Dica:** Para desenvolvimento iterativo sem rebuildar a imagem:
> ```bash
> docker run --rm -v $(pwd)/src:/lab/src lab-aula-XX
> ```

Veja instruções detalhadas em [`Help.md`](./Help.md) e no README de cada lab.

---

💡 *O mundo movimenta quintilhões de bytes por dia. Preparem-se para dominar essa infraestrutura!*