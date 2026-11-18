# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

- Rafael Nogueira Maruca - RA 6322006
- Gabriel De Souza Oliveira - RA 6325262
- Matheus Borali - RA 6325135

## Problema

**Projeto: plataforma de dados para uma rede de lojas de autopeças.**

Uma rede de lojas de autopeças lida todos os dias com milhares de
vendas no balcão e na loja online, dezenas de milhares de itens em
estoque espalhados entre o depósito e as lojas, uma base grande de
clientes e muitos comentários e avaliações. Hoje essas informações
ficam separadas em sistemas diferentes e as decisões são tomadas "no
feeling" do gerente. Isso causa três problemas principais:

1. **Falta e sobra de estoque:** quando uma peça acaba, o cliente compra
   no concorrente e a venda é perdida. Ao mesmo tempo, peças de pouca
   saída ficam meses paradas no depósito, prendendo dinheiro.
2. **Cliente esquecido:** peças como pastilha de freio, filtro de óleo,
   correia e bateria têm troca periódica, mas a loja não avisa o cliente
   quando a próxima troca se aproxima e perde a venda recorrente.
3. **Reclamações sem análise:** comentários de clientes (loja online,
   WhatsApp, avaliações) não são lidos de forma organizada, e problemas
   como "peça errada para o meu carro" ou "entrega atrasada" se repetem.

O problema é relevante porque o setor de reposição automotiva é grande
no Brasil, a frota é antiga e cada carro usa peças diferentes por marca,
modelo e ano, o que gera um volume e uma variedade de dados que não cabe
em uma planilha. A proposta é construir uma **plataforma de dados** que
receba esses eventos em tempo real, guarde o histórico em um Data Lake,
aplique Machine Learning e NLP e entregue as respostas para quem decide:
o gerente (dashboard), o comprador (quanto pedir ao fornecedor) e o
cliente (mensagem no momento certo).

O foco **não** é construir o sistema de cadastro/ERP da loja, e sim a
camada de dados e de inteligência que fica por cima dele.

## Objetivos

1. **Pipeline de ingestão em tempo real:** receber vendas, movimentações
   de estoque e comentários como eventos no Kafka e processá-los com
   Spark Streaming, atualizando o estoque de cada peça por loja em menos
   de 1 minuto após a venda.
2. **Data Lake organizado em camadas** (raw → tratada → analítica) em
   Parquet particionado por data e loja, com tabelas consultáveis por
   SQL (Hive / Spark SQL).
3. **Previsão de demanda:** treinar um modelo no Spark MLlib que preveja
   a quantidade vendida de cada peça por loja no próximo mês, com meta de
   **erro percentual médio (MAPE) abaixo de 20%** nas peças de maior
   giro, e comparar com a média simples dos últimos meses (baseline).
4. **Alerta de estoque mínimo:** gerar automaticamente um alerta de
   reposição quando a previsão indicar que uma peça vai acabar antes da
   próxima entrega do fornecedor.
5. **Peças compradas juntas:** descobrir combinações frequentes (ex.:
   pastilha + disco de freio) com o algoritmo FP-Growth do MLlib, para
   sugerir venda casada no balcão e na loja online.
6. **Lembrete de troca para o cliente:** identificar clientes cuja troca
   periódica está próxima (pelo histórico de compras e o intervalo de
   troca de cada tipo de peça) e gerar a lista de mensagens a enviar.
7. **Análise dos comentários com NLP:** classificar o sentimento dos
   comentários e encontrar os assuntos mais citados nas reclamações.
8. **Dashboard final** no Apache Superset com estoque crítico, previsão
   × venda real, ranking de peças e lojas, combinações de peças e
   satisfação dos clientes.

## Dataset(s) e Fonte

Dados reais de uma loja (vendas, clientes, estoque) são privados e
protegidos pela LGPD, por isso o projeto vai usar **dados sintéticos
gerados pelo grupo**, construídos para se parecerem com a realidade e
**ancorados em fontes públicas reais**:

| Base | Fonte | Volume aproximado |
|---|---|---|
| Modelos de veículos (marca, modelo, ano) | **API pública da Tabela FIPE** (real) | ~10 mil versões de veículos |
| Frota por modelo e município (peso de cada modelo nas vendas) | **Dados abertos da Senatran** (real) | milhões de linhas, filtradas para o estado de SP |
| Endereços dos clientes (CEP, cidade, bairro) | **API ViaCEP** (real) + Faker | 50 mil clientes |
| Catálogo de peças e compatibilidade peça ↔ veículo | Sintético (gerado em Python) | 20 mil peças |
| Vendas (balcão e loja online) | Sintético (gerado em Python) | **~5 milhões de itens vendidos em 3 anos, 10 lojas** |
| Movimentações de estoque (entradas, saídas, transferências) | Sintético | ~8 milhões de eventos |
| Comentários e avaliações dos clientes, em português | Sintético a partir de modelos de frase | ~200 mil comentários |

O gerador vai incluir padrões realistas: sazonalidade (mais baterias no
inverno, mais itens de ar-condicionado no verão), modelos mais comuns na
frota vendendo mais peças, intervalo de troca por tipo de peça e ruído
aleatório. O volume total fica na casa de **alguns GB**, e o gerador
permite aumentar a escala (mais lojas, mais anos) para testar o
pipeline com volumes maiores.

## Ferramentas de Big Data

| Ferramenta | Uso no projeto | Por que faz sentido |
|---|---|---|
| **Apache Kafka** | Tópicos `vendas`, `estoque` e `comentarios`, alimentados por um produtor que simula as lojas | Cada venda é um evento que chega a qualquer hora, de várias lojas ao mesmo tempo. O Kafka desacopla as lojas do processamento e aguenta picos (ex.: sábado de manhã) |
| **Spark Structured Streaming** | Consome os tópicos, atualiza o saldo de estoque por peça e loja e dispara o alerta de estoque mínimo | O estoque precisa ser atualizado em tempo real para que o alerta chegue antes da peça acabar |
| **HDFS / S3 (Data Lake)** | Armazena o histórico nas camadas raw, tratada e analítica em Parquet | Milhões de eventos por ano não cabem num banco relacional comum para análise. O Data Lake guarda o dado bruto e permite reprocessar |
| **Apache Spark (DataFrames / Spark SQL)** | Limpeza, padronização e junção de vendas, peças, veículos e clientes | Processamento distribuído e em memória sobre milhões de linhas |
| **MongoDB** | Catálogo de peças, cadastro de clientes e comentários | Cada peça tem atributos diferentes (medidas, compatibilidade com vários modelos) e cada comentário é texto livre: o modelo de documentos é mais natural que tabelas fixas |
| **Hive (Spark SQL com suporte a Hive)** | Tabelas externas sobre o Data Lake para relatórios em SQL | Permite que analistas consultem o histórico com SQL, no estilo Data Warehouse |
| **Spark MLlib** | Regressão para **previsão de demanda** e **FP-Growth** para peças compradas juntas | Treinar modelos de forma distribuída sobre todo o histórico de vendas de todas as lojas |
| **NLP** (tokenização, stopwords, stemming, sentimento por léxico) | Sentimento e assuntos dos comentários, aplicados em paralelo com UDFs do Spark | O texto dos clientes é dado não estruturado e precisa ser transformado em indicadores |
| **Apache Superset** | Dashboard do gerente e do comprador | Transforma os resultados em decisões visuais e acessíveis para quem não é técnico |
| **Docker / Docker Compose** | Sobe Kafka, Spark, MongoDB e Superset de forma padronizada | Mesmo ambiente na máquina de cada integrante e na faculdade |

**APIs utilizadas:**

- **API da Tabela FIPE** (pública e gratuita): lista real de marcas,
  modelos e anos, usada para montar a compatibilidade das peças.
- **ViaCEP** (pública e gratuita): padronização dos endereços dos
  clientes.
- **WhatsApp Business Cloud API (Meta)**: canal para os lembretes de
  troca e avisos de pedido. No projeto, o envio será **simulado**
  (as mensagens são geradas e gravadas em um tópico Kafka
  `mensagens_cliente`), deixando a integração real como próximo passo.
- Integrações futuras citadas na arquitetura: API de consulta de placa
  (identificar o carro do cliente pela placa), Correios/Melhor Envio
  (frete) e API do Mercado Livre (vendas em marketplace).

**Arquitetura resumida:**

```
Lojas / loja online / WhatsApp
          │  (produtor que simula os eventos)
          ▼
       Kafka  ──►  Spark Streaming  ──►  alerta de estoque / mensagens ao cliente
          │
          ▼
Data Lake (raw → tratada → analítica, Parquet)  +  MongoDB (catálogo, clientes, comentários)
          │
          ▼
Spark SQL / Hive  ──►  MLlib (demanda, FP-Growth)  +  NLP (comentários)
          │
          ▼
      Apache Superset (dashboard)
```

## Cronograma

| Aula | Etapa | Entregas |
|---|---|---|
| **Aula 11** | Definição e planejamento | Problema, objetivos, arquitetura, escolha das ferramentas e das APIs (esta proposta) |
| **Aula 12** | Ingestão e pré-processamento | Gerador de dados sintéticos ancorado na FIPE, Senatran e ViaCEP; produtor Kafka; Spark Streaming atualizando o estoque; Data Lake em camadas; carga do MongoDB |
| **Aula 13** | Análise e construção de modelos | Consultas no Hive / Spark SQL; previsão de demanda no MLlib comparada ao baseline; FP-Growth das peças compradas juntas; NLP dos comentários; regra de lembrete de troca |
| **Aula 14** | Visualização e conclusão | Dashboard no Superset; demonstração do alerta de estoque e das mensagens simuladas; relatório final; apresentação dos resultados e lições aprendidas |
