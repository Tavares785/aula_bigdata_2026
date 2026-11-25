# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

- Rafael Nogueira Maruca - RA 6322006
- Gabriel de Souza Oliveira - RA 6325262
- Caio Akiyama - RA 6325124

## Problema

**Projeto: por que as entregas da MercadoFácil atrasam e quanto isso custa.**

A MercadoFácil é um e-commerce brasileiro de médio porte que vende pelo
app, pelo site e por parceiros de marketplace. Em 2025 a diretoria notou
três sintomas:

1. **Aumento de atrasos nas entregas**, principalmente no Norte/Nordeste e
   em novembro/dezembro (Black Friday e Natal);
2. **Avaliações baixas** e comentários negativos concentrados em pedidos
   atrasados;
3. **Cancelamentos e devoluções acima da meta**, sem saber quais
   categorias, canais ou regiões mais pesam.

Hoje os dados de pedido, cliente, produto, pagamento, logística e
avaliação chegam juntos num dump bruto e "sujo" (datas em vários formatos,
valores com `R$`, categorias escritas de formas diferentes, duplicados e
dados pessoais), e ninguém consegue responder com segurança onde e por que
a operação falha. O problema é relevante porque cada atraso inesperado
derruba a nota do cliente e a reputação da loja, e a alta temporada é
justamente quando a empresa mais vende.

Como time de dados, vamos construir um pipeline de Big Data na AWS que
transforme esse dump em informação confiável, explique os atrasos (por
região, transportadora, sazonalidade, chuva e feriados), meça o efeito do
atraso na nota e nas devoluções e entregue um dashboard e recomendações
para a diretoria.

## Objetivos

1. **Pipeline medalhão na AWS (raw → silver → gold)**, criado com
   Terraform: as 10.000 linhas do dump limpas, tipadas e deduplicadas, com
   pelo menos 6 regras de qualidade documentadas, quarentena para as linhas
   inválidas (com o motivo) e dados pessoais protegidos (LGPD).
2. **Camada gold no Athena** com views que respondam às perguntas da
   diretoria: KPIs do negócio, nota por faixa de atraso, série diária
   (Black Friday/Natal), logística por estado e transportadora,
   cancelamento/devolução por categoria e canal, e o efeito da chuva e dos
   feriados.
3. **Medir o custo do atraso:** comparar a nota média de itens entregues no
   prazo e com 1–3, 4–7 e 8+ dias de atraso.
4. **Prever o risco de atraso no momento da compra** com Spark MLlib
   (Regressão Logística × Random Forest), com meta de **AUC ≥ 0,65** e
   olhando recall e precisão da classe "atrasou", sem vazamento de
   informação.
5. **NLP nos comentários** (tokenização, stopwords, sentimento por léxico)
   para medir quanto as reclamações citam atraso, defeito e atendimento.
6. **Dashboard interativo no Apache Superset** com pelo menos 6 gráficos e
   um filtro nativo, e **3 insights com números** que virem recomendações
   de negócio.

## Dataset(s) e Fonte

| Base | Fonte | Volume |
|---|---|---|
| `pedidos_mercadofacil.csv` (dump bruto) | Fornecido pelo professor (Aula 12) | 10.000 itens de pedido, 33 colunas, ano de 2025 |
| `pedidos_mercadofacil_tratado.csv` (base tratada) | Fornecido pelo professor (Aula 14) | 10.000 itens, ~7,2 mil pedidos, 28 colunas, sem dados pessoais |
| `chuva_diaria` | API pública **Open-Meteo** (histórico de 2025), coletada pelo professor | ~8.400 linhas (cidade × dia), chuva do dia e dos 3 dias |
| `feriados` | API pública **BrasilAPI** (feriados nacionais de 2025) | 14 feriados |

Uma linha do dump é um item de pedido; os dados do pedido e do cliente se
repetem em cada item. O dump contém dados pessoais fictícios (nome, e-mail e
CPF), tratados conforme a LGPD antes de seguir para as camadas analíticas.
O pipeline é escrito para escalar: o mesmo código roda com milhões de
linhas, bastando aumentar os workers do Glue.

## Ferramentas de Big Data

| Ferramenta | Uso no projeto | Por que faz sentido |
|---|---|---|
| **Terraform** (provider AWS 5.31.0) | Cria e destrói toda a infraestrutura | Ambiente reprodutível e sem custo residual no Learner Lab (`apply` sobe, `destroy` apaga) |
| **Amazon S3** | Data lake com as camadas raw, silver, gold e quarentena | Armazenamento distribuído e barato; o raw nunca é alterado, então dá para reprocessar |
| **AWS Glue Job (PySpark)** | ETL raw → silver → gold | Spark gerenciado: processamento distribuído sem manter cluster ligado (o EMR Serverless é bloqueado no lab) |
| **Glue Crawler + Data Catalog** | Registra as tabelas Parquet | Deixa os dados consultáveis por SQL sem cadastro manual |
| **Amazon Athena** | Views da camada gold | SQL sobre o data lake (estilo Hive), cobrado por consulta |
| **Spark MLlib** | Modelo de risco de atraso | Treino distribuído sobre todo o histórico |
| **NLP** (tokenização, stopwords, sentimento) | Análise dos comentários | O texto livre dos clientes vira indicador (sentimento e temas de reclamação) |
| **Apache Superset** (EC2) | Dashboard interativo conectado ao Athena | Ferramenta de BI open source vista no curso, com filtros nativos |

## Cronograma

| Aula | Etapa | Entregas |
|---|---|---|
| **Aula 11** | Definição e planejamento | Problema, objetivos, dados e ferramentas (esta proposta) |
| **Aula 12** | Ingestão e pré-processamento | Terraform, Glue Job raw → silver/quarentena → gold, Crawler, consultas no Athena e `REGRAS_SILVER.md` |
| **Aula 13** | Análise e modelos | Modelo de risco de atraso no MLlib e NLP dos comentários |
| **Aula 14** | Visualização e conclusão | Views no Athena, dashboard no Superset, relatório final e pitch de 8 minutos |
