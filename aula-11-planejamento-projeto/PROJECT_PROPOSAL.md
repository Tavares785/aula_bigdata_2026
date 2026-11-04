# Proposta de Projeto de Big Data

## Integrantes do Grupo

- José Henrique Teixeira Luiz — RA 3225002
- Daniel de Oliveira Tavares Júnior — RA 6325032
- Leandro Duarte — RA 6325072

## Problema

**Quantas empresas brasileiras param de operar sem dar baixa, e o que
as distingue das que continuam ativas?**

A Receita Federal publica o Cadastro Nacional da Pessoa Jurídica como
dado aberto: cerca de 60 milhões de estabelecimentos, com situação
cadastral, CNAE, município, porte, data de abertura e data da situação
atual. O cadastro registra `ATIVA`, `BAIXADA`, `SUSPENSA`, `INAPTA` e
`NULA` — mas a transição entre elas não é imediata nem automática.

O caso que interessa é a empresa **inapta**: ela deixou de entregar
declaração, a Receita a marcou, e ela segue no cadastro como se
existisse. Para quem consulta um CNPJ antes de fechar negócio, `INAPTA`
e `ATIVA` são linhas parecidas num cadastro — e a diferença decide se
há risco na operação.

O problema é relevante por três razões concretas:

1. **Escala que não cabe em ferramenta comum.** O dump trimestral da
   Receita tem dezenas de gigabytes distribuídos em arquivos de
   estabelecimentos, empresas, sócios e tabelas auxiliares. Abrir isso
   em planilha ou num banco relacional sem particionamento não é
   possível — é exatamente o cenário que justifica Hadoop e Spark.

2. **Decisão real depende disso.** Habilitação cadastral é pré-requisito
   em contratação pública, em crédito e em cadastro de fornecedor.

3. **O dado é público e verificável.** Não dependemos de acesso privado
   nem de dado sintético, e qualquer pessoa pode reproduzir o resultado.

## Objetivos

Cada objetivo tem uma forma de medir se foi alcançado.

| # | Objetivo | Como medimos |
|---|---|---|
| 1 | Carregar o dump completo do CNPJ em HDFS e normalizá-lo com Spark | Contagem de estabelecimentos no Hive igual à soma das linhas dos CSV de origem, com o descarte justificado linha a linha |
| 2 | Medir a distribuição de situação cadastral por CNAE, porte, município e ano de abertura | Tabela agregada no Hive respondendo em menos de 30 s para qualquer corte |
| 3 | Medir o **tempo entre a inaptidão e a baixa efetiva**, por faixa de porte | Mediana e P90 em dias, por porte, com o número de empresas que sustenta cada faixa |
| 4 | Treinar um classificador que estime a chance de uma empresa ativa estar inapta em 12 meses | AUC-ROC em conjunto de teste separado por tempo, comparado a uma linha de base ingênua |
| 5 | Publicar um painel que responda às perguntas acima sem consulta manual | Painel no Superset com os cortes do objetivo 2 e a série do objetivo 3 |

O objetivo 4 merece uma ressalva: **não prometemos acurácia alta.** O
cadastro não traz a causa da inaptidão, então um modelo só com dados
cadastrais tem teto baixo por construção. A entrega é a comparação
honesta contra a linha de base — se o modelo não superá-la, isso é
resultado, e vamos relatá-lo como tal.

**O que este projeto NÃO faz.**

- Não afirma causalidade. Correlação entre CNAE e inaptidão não diz que
  o ramo causa a inaptidão.
- Não identifica empresa individual como risco. O resultado é
  estatístico, por grupo; apontar CNPJ específico com base nisso seria
  uso indevido.
- Não usa dado de sócio pessoa física além do que é público e agregado.

## Dataset(s) e Fonte

**Principal — Dados Abertos do CNPJ (Receita Federal)**

- Origem: `https://dadosabertos.rfb.gov.br/CNPJ/`
- Formato: CSV separado por `;`, codificação Latin-1, sem cabeçalho
  (o layout vem em PDF à parte)
- Volume: ~6 GB comprimido, **~40 GB descomprimido**
- Granularidade: ~60 milhões de estabelecimentos, ~50 milhões de
  empresas, ~24 milhões de sócios
- Atualização: trimestral

Arquivos que vamos usar:

| Arquivo | Conteúdo | Para quê |
|---|---|---|
| `Estabelecimentos` | situação cadastral, data da situação, CNAE, município | base da análise |
| `Empresas` | razão social, porte, capital social, natureza jurídica | atributos do modelo |
| `Simples` | opção pelo Simples Nacional e MEI | corte por regime |
| `Cnaes`, `Municipios`, `Motivos` | tabelas de domínio | tradução dos códigos |

**Complementar — BrasilAPI**

- Origem: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`
- Uso: **validação por amostragem.** Sorteamos alguns milhares de CNPJ
  do nosso HDFS e comparamos a situação cadastral com a resposta da API.
  Divergência alta indicaria dump desatualizado ou erro na nossa carga —
  é a checagem que impede confiar num ETL que silenciosamente perdeu
  linhas.

**Três armadilhas que já identificamos no dado:**

1. **Latin-1, não UTF-8.** Ler como UTF-8 corrompe acento em razão
   social e nome de município, e o erro só aparece nas agregações por
   nome.
2. **Data como `AAAAMMDD` em texto, com `0` para ausente.** Converter
   sem tratar o zero gera data no ano 0, que entra nas médias e as
   destrói.
3. **O CNPJ está partido em três colunas** (básico, ordem, DV). Juntar
   na ordem errada produz CNPJ válido em formato e inexistente de fato —
   erro que passa em qualquer validação de dígito.

## Ferramentas de Big Data

Cada ferramenta entra por um motivo, não por estar na lista da matéria.

**HDFS (Hadoop)** — armazenar os CSV brutos particionados. É o único
componente do curso feito para arquivo grande, sequencial e imutável, e
o dump da Receita é exatamente isso. Guardamos o bruto intacto: refazer
a transformação sem rebaixar o download é o que permite corrigir um erro
de ETL sem perder um dia.

**Spark (DataFrames + Spark SQL)** — a transformação. Tipagem das
colunas, junção dos quatro arquivos pela chave do CNPJ, cálculo do
intervalo entre inaptidão e baixa. Spark porque a junção de 60 milhões
por 50 milhões de linhas não cabe em memória de uma máquina, e ele
resolve isso particionando.

**Hive** — a camada de consulta sobre o resultado, particionada por UF e
ano. É o que permite a pergunta ad hoc do objetivo 2 sem reprocessar o
Spark a cada corte.

**MongoDB** — a camada de serviço para consulta por CNPJ. O Hive é bom
para varredura analítica e ruim para "me dê este registro agora"; o
Mongo faz o oposto. Guardamos ali o resultado por estabelecimento, com
índice no CNPJ.

**Kafka** — a parte honestamente **simulada**. O dado real é trimestral,
não um fluxo. Vamos reproduzir a mudança de situação cadastral como
stream, comparando dois dumps consecutivos e emitindo um evento por
transição, para exercitar consumo em janela e detecção de mudança. Está
declarado como simulação porque chamar isso de tempo real seria falso.

**MLlib** — o classificador do objetivo 4. Regressão logística como
linha de base e gradient boosting para comparar, com separação temporal
entre treino e teste: treinar com dump antigo e testar no novo. Separar
aleatoriamente deixaria o modelo ver o futuro e inflaria a métrica.

**NLP** — análise da razão social. Pergunta concreta: termos no nome da
empresa se associam a maior taxa de inaptidão? Tokenização, remoção de
termos societários (`LTDA`, `ME`, `EIRELI`) e TF-IDF por grupo de
situação.

**Superset** — o painel do objetivo 5. Escolhido em vez do Zeppelin
porque a entrega é painel para quem não escreve código, e o Zeppelin é
notebook.

## Cronograma

Quatro etapas, com entrega verificável em cada uma. As datas assumem
início na semana seguinte à aprovação da proposta.

| # | Etapa | Semanas | Entrega verificável | Responsável |
|---|---|---|---|---|
| 1 | Ingestão e carga em HDFS | 1–2 | Contagem no HDFS igual à origem; as três armadilhas de formato tratadas e testadas | José |
| 2 | ETL no Spark e tabelas no Hive | 3–4 | Tabela particionada responde aos cortes do objetivo 2; validação por amostragem contra a BrasilAPI com divergência medida | José e Daniel |
| 3 | Modelo e NLP | 5–6 | AUC-ROC do modelo **e da linha de base**, lado a lado; TF-IDF por grupo de situação | Daniel |
| 4 | Painel, stream simulado e apresentação | 7–8 | Painel no Superset com os cortes definidos; consumidor Kafka processando as transições entre dois dumps | Leandro e José |

**Marco de decisão no fim da etapa 2.** Se a validação por amostragem
mostrar divergência acima de 5% contra a BrasilAPI, paramos e
investigamos o ETL antes de treinar qualquer modelo. Modelo treinado em
dado carregado errado produz métrica bonita e conclusão inválida, e o
erro fica invisível até alguém conferir a origem.

**Risco principal e o que fazemos com ele.** Quarenta gigabytes não
cabem confortavelmente numa máquina de estudante. O plano é processar um
**recorte por UF** (São Paulo primeiro, ~15 milhões de estabelecimentos)
em ambiente local, e só então decidir se o conjunto nacional roda. Se
não rodar, o recorte estadual é a entrega — com o escopo declarado no
relatório, não escondido.
