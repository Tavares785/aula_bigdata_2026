# Relatório Final do Projeto de Big Data

> Preencha cada seção, substituindo `<PREENCHER>`, e marque os itens do
> checklist trocando `[ ]` por `[x]` conforme forem concluídos. Não
> remova os títulos (`##`).

**Grupo:** Weslley Lucas (RA 6325226), Gabriel Reis Cunha (RA 6325149) e
Sirlande Martins (RA 6325269). Projeto MercadoFácil, base
`pedidos_mercadofacil_tratado.csv` (10.000 itens, 2025).

## Resumo dos Resultados

**Contexto.** A diretoria da MercadoFácil quer saber onde e por que as
entregas atrasam, quanto o atraso custa em nota e devoluções, e como a Black
Friday e o Natal pressionam a operação. Em 2025, a empresa faturou
**R$ 3.297.891,59** em itens entregues. Foram **6.706 pedidos**, com ticket
médio de **R$ 491,78**. Atrasaram **16,3%** dos itens entregues. A nota média
é **4,11** e **7,6%** dos itens foram cancelados ou devolvidos (`vw_kpis`).

**O que os dados mostram.**

1. **O atraso derruba a nota e aumenta a devolução.** Itens no prazo têm nota
   **4,39**. A nota cai para 3,59 com 1 a 3 dias de atraso, 2,35 com 4 a 7
   dias e **1,24** com 8 ou mais (`vw_atraso_nota`). A devolução segue o mesmo
   padrão: 3,0% dos itens no prazo são devolvidos, contra **16,2%** dos que
   atrasam 8 ou mais dias.
2. **O atraso se concentra no Norte e em duas transportadoras.** O Norte tem
   atraso médio de **1,38 dia** e 24,2% de itens atrasados. O Sudeste tem
   0,62 dia e 14,4% (`vw_logistica_estado`). Os Correios atrasam **20,1%** dos
   itens e a Entrega Própria, **11,0%**. A diferença se mantém dentro do
   Sudeste: 0,84 contra 0,31 dia. O pior par é **Jadlog no Norte**, com
   2,24 dias e 38,9% de itens atrasados (`vw_transportadora`, view bônus).
3. **A chuva acompanha o atraso, mas não prova causa sozinha.** Pedidos sem
   chuva no destino (menos de 5 mm em 3 dias) atrasam **0,49 dia** em média.
   Com 40 mm ou mais, atrasam **1,93 dia**, e o percentual de itens atrasados
   sobe de 12,8% para 31,5% (`vw_atraso_chuva`). A região não explica isso
   sozinha. Dentro do Sudeste, o atraso vai de 0,38 para 1,99 dia conforme a
   chuva aumenta. No Norte, vai de 0,69 para 2,08 (`vw_atraso_chuva_regiao`).
   A região também pesa: sem chuva, o Norte atrasa 0,69 dia e o Sudeste,
   0,38. É uma **correlação forte e consistente**, que cresce com a
   intensidade da chuva. Mas o dado é observacional, então não prova causa.
   Chuva, estrada e transportadora andam juntas.
4. **Datas de pico pressionam a operação.** Na Black Friday (28/11), foram
   **160 pedidos** no dia, cerca de 8 vezes a média de 18,4 pedidos/dia.
   Novembro e dezembro têm cerca de 850 pedidos cada, contra cerca de 500 nos
   outros meses (+70%) (`vw_serie_diaria`). Em feriados, entram **21,9
   pedidos/dia**, contra 18,2 em dias comuns, e o atraso médio sobe de 0,71
   para **1,12 dia** (`vw_feriados`). Aqui também é correlação: são só 14
   dias de feriado, e o Natal coincide com o pico de dezembro.
5. **Cancelamento e devolução por categoria e canal.** Beleza e Saúde tem o
   maior cancelamento (4,97%) e Brinquedos, a maior devolução (4,62%). O
   canal `marketplace_parceiro` devolve **5,07%** dos itens, contra 3,61% do
   `app` (`vw_problemas_categoria`).

**O que fazer (recomendação).**

- **Transportadora:** tirar volume dos Correios e da Jadlog no Norte e passar
  para Loggi ou Entrega Própria onde houver cobertura, com meta de
  pontualidade em contrato. Se o Norte chegasse ao nível do Sudeste (14,4% de
  itens atrasados), sairiam cerca de 38 itens atrasados por ano só nessa
  região, justamente os de pior nota.
- **Prazo dinâmico com previsão do tempo:** quando a previsão para o destino
  passar de 20 mm em 3 dias, somar 1 dia ao prazo prometido e avisar o
  cliente. Prometer um prazo realista protege a nota mais que atrasar em
  silêncio.
- **Capacidade sazonal:** reforçar a expedição e as transportadoras de
  novembro a dezembro, quando entram cerca de 70% mais pedidos. A Black
  Friday exige um plano próprio para um dia com 8 vezes o volume normal.
- **Validar causa antes de investir:** fazer um teste A/B do prazo dinâmico
  em parte das cidades com chuva forte para medir o efeito real na nota.

## Visualizações Criadas

Dashboard **"MercadoFacil 2025 - atraso, nota e sazonalidade"** no **Apache
Superset 3.1**, rodando em EC2. Ele está ligado ao **Athena** (workgroup
`wg-aula14-...`, banco `mercadofacil_aula14`), que lê o CSV no S3 pelo Glue
Catalog. São 14 gráficos, todos alimentados pelas views gold de
`aws-lab/sql/02_views_prontas.sql` e `aws-lab/sql/03_views_atividade.sql`.

| # | Gráfico (tipo) | View | O que mostra | Decisão que apoia |
|---|---|---|---|---|
| 1-6 | Big Numbers: receita, pedidos, ticket, % atrasados, nota, % cancelado/devolvido | `vw_kpis` | Saúde geral do negócio em 2025 | Acompanhar as metas da diretoria |
| 7 | Linha diária, com zoom | `vw_serie_diaria` | Pico na Black Friday (28/11) e alta em nov–dez | Planejar a capacidade sazonal |
| 8 | Barras | `vw_atraso_nota` | Nota cai de 4,39 para 1,24 conforme o atraso | Justificar o investimento em pontualidade |
| 9 | Barras agrupadas (região × transportadora) | `vw_logistica_estado` | Norte e Correios/Jadlog com mais atraso | Renegociar ou trocar a transportadora |
| 10 | Barras empilhadas (% cancelado + % devolvido) | `vw_problemas_categoria` | Categorias com mais problemas | Revisar anúncios e qualidade por categoria |
| 11 | Barras | `vw_atraso_chuva` | Atraso cresce com a chuva (0,49 → 1,93 dia) | Prazo dinâmico com previsão do tempo |
| 12 | Barras agrupadas (chuva × região) | `vw_atraso_chuva_regiao` | O efeito da chuva aparece dentro de cada região | Separar chuva de região (causa × correlação) |
| 13 | Barras (bônus) | `vw_transportadora` | % de itens atrasados por transportadora | Escolher a transportadora por região |
| 14 | Barras | `vw_feriados` | Pedidos/dia em feriado × dia comum | Escala em feriados |

**Filtros nativos:**

- **Região** (`regiao`): afeta os gráficos 9, 12 e 13. O print
  `evidencias/03_...` mostra o filtro em uso com "Norte".
- **Categoria** (`categoria`): afeta o gráfico 10.
- **Zoom** no eixo do tempo do gráfico 7.

O script `aws-lab/scripts/superset_dashboard.py` recria datasets, gráficos e
dashboard pela API REST do Superset. Assim o dashboard é reprodutível depois
do `destroy`.

Como **Plano B**, o `aws-lab/scripts/dashboard_local.py` gera o mesmo resumo
em HTML a partir do CSV (`evidencias/06_plano_b_dashboard_local.png`).

**Evidências** (`evidencias/`, sem credenciais e com IP e conta mascarados):

- `01_terraform_apply.png`
- `02_superset_dashboard_completo.png`
- `03_superset_dashboard_filtro_regiao_norte.png`
- `04_athena_consulta_sqllab.png`: consulta à `vw_atraso_chuva` no Athena
  pelo SQL Lab
- `05_terraform_destroy.png`
- `06_plano_b_dashboard_local.png`

## Lições Aprendidas

- **Infra como código paga a conta.** Um `terraform apply` sobe S3, Glue,
  Athena e Superset em poucos minutos, e um `destroy` apaga tudo: 8 recursos
  criados e 8 destruídos. Sem isso, o Learner Lab, com sessão curta e
  orçamento limitado, seria inviável. No WSL, o Terraform falhou ao ler o
  módulo em `/mnt/c` ("Failed to read directory for module"). A solução foi
  rodar de uma cópia no disco Linux, com `TF_DATA_DIR` também no Linux.
- **A camada gold é onde mora a regra de negócio.** O denominador de cada
  métrica muda o resultado. Receita, ticket, atraso e nota usam só itens
  entregues. Cancelamento e devolução usam todos os itens. Os pedidos
  contam `DISTINCT pedido_id`, porque cada linha é um item. No Athena (Trino),
  dividir dois inteiros dá inteiro, então usamos `* 1.0` e `100.0`. Para
  somar percentuais entre grupos, ponderamos pelo número de itens
  (`SUM(itens * pct) / SUM(itens)`) em vez de tirar a média das médias.
- **Validar antes de publicar.** Rodamos as views primeiro em DuckDB local e
  depois no Athena, e os números bateram. Também conferimos que o JOIN com a
  chuva casa as 10.000 linhas sem nenhuma faltando (`01_validar.sql`).
- **Correlação não é causa.** O gráfico de chuva sozinho sugeria uma causa
  simples. Ao quebrar por região, vimos que o efeito continua dentro de cada
  região, mas que a região também soma. A recomendação, por isso, inclui um
  teste A/B em vez de uma afirmação causal.
- **Visualização para a diretoria.** Títulos em forma de pergunta ou
  resposta, eixos com unidade e um filtro que muda vários gráficos ajudaram
  mais que gráficos sofisticados. Ordenar as faixas com prefixo (`1)`, `2)`)
  evitou a ordem alfabética errada.
- **Equipe e o que faríamos diferente.** Dividimos o trabalho em
  SQL/validação, dashboard e relatório/pitch. Faríamos diferente: escrever o
  dashboard como código desde o início (API do Superset) e combinar antes as
  definições de métrica, para não refazer views.

## Referências

- Base `aws-lab/data/pedidos_mercadofacil_tratado.csv` (material da
  disciplina) e camadas das Aulas 12 e 13 do grupo.
- Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- BrasilAPI, Feriados Nacionais: https://brasilapi.com.br/docs#tag/Feriados-Nacionais
- Amazon Athena (Trino) SQL reference: https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html
- AWS Glue Data Catalog: https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html
- Apache Superset, documentação e REST API: https://superset.apache.org/docs/api
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- DuckDB (validação local das views): https://duckdb.org/docs/
- Knaflic, C. N. *Storytelling with Data*. Wiley, 2015.

## Checklist de Entregáveis

- [x] Pelo menos uma visualização/dashboard interativo foi criado
      (Zeppelin ou Superset)
- [x] O dashboard/visualização foi conectado aos dados processados nas
      etapas anteriores (Aulas 12 e 13) ou à base tratada fornecida na
      Aula 14 (`pedidos_mercadofacil_tratado.csv`)
- [x] A apresentação final do projeto está pronta
- [x] Print(s) ou link de acesso ao dashboard foram anexados a esta PR
      (comentário ou pasta `evidencias/`, à escolha do grupo)
