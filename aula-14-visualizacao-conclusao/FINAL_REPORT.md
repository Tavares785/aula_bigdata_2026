# Relatório Final do Projeto de Big Data

**Grupo:** José Henrique Teixeira Luiz (RA 3225002), Daniel Tavares (RA 6325032), Leandro Duarte (RA 6325072)
**Base:** `pedidos_mercadofacil_tratado.csv` — 10.000 itens de pedido, 7.255 pedidos, jan–dez/2025
**Dados de apoio:** `chuva_diaria` (Open-Meteo Archive) e `feriados` (BrasilAPI)

## Resumo dos Resultados

**Contexto.** A MercadoFácil entregou R$ 3.297.891,59 em 2025 (6.706 pedidos entregues,
ticket médio de R$ 491,78) e perdeu R$ 280.428,20 em itens cancelados e devolvidos — 7,8%
do faturamento bruto. A nota média é 4,11. A diretoria queria saber onde e por que as
entregas atrasam, quanto o atraso custa, e como a Black Friday e o Natal pressionam a
operação. 16,27% dos itens entregues chegaram atrasados.

### Insight 1 — O atraso não incomoda o cliente, ele o faz devolver

A nota cai monotonicamente com o atraso: **4,39** no prazo, 3,59 com 1-3 dias, 2,35 com
4-7 dias e **1,24 com 8 dias ou mais** — uma queda de 3,15 pontos entre os extremos.

O que transforma isso em dinheiro é a devolução. A taxa de devolução é de **3,03% nos itens
entregues no prazo e 9,94% nos atrasados**, chegando a 16,2% acima de 8 dias. Dos 1.670
itens atrasados, 166 foram devolvidos; na taxa do prazo seriam 50,6. São **115 devoluções
excedentes atribuíveis ao atraso**, que ao ticket médio de devolução de R$ 377,47 valem
**R$ 43.548 por ano** — sem contar o frete reverso nem o cliente que não volta.

### Insight 2 — A chuva atrasa de verdade, e o efeito sobrevive aos dois confundidores óbvios

Usando `chuva_3d_mm` (chuva do dia do pedido mais os dois seguintes, que é a janela da
coleta e da primeira perna do frete), o atraso cresce com a chuva:

| Faixa de chuva | Itens | Atraso médio | % atrasados |
|---|---:|---:|---:|
| sem chuva (<5 mm) | 4.677 | 0,49 d | 12,8% |
| fraca (5-20) | 2.840 | 0,68 d | 15,7% |
| forte (20-40) | 1.187 | 1,21 d | 24,4% |
| muito forte (40+) | 540 | 1,93 d | **31,5%** |

Correlação não basta, e havia duas explicações alternativas plausíveis. Testamos as duas:

- **"É a região, não a chuva."** Manaus e Belém chovem muito e ficam longe dos centros de
  distribuição. A view bônus `vw_atraso_chuva_regiao` estratifica por região, e dentro de
  cada uma o gradiente permanece: no Sudeste, que tem 5.444 itens e é onde o dado é mais
  firme, vai de **10,6% sem chuva a 33,2% na chuva muito forte**. No Norte, 14,7% → 31,7%.
- **"É o pico de novembro e dezembro."** Removendo nov/dez: 10,8% → 27,4%. Olhando só
  nov/dez: 19,6% → 37,4%. O gradiente aparece dos dois lados. E a chuva forte nem se
  concentra no pico: janeiro tem 34,3% dos itens em chuva forte e dezembro 31,5%, mas
  agosto tem 5,8%.

**É correlação robusta, não causalidade provada** — faltam o trânsito, o estado da via e o
efetivo da transportadora no dia. Mas sobreviver aos dois confundidores testados é mais do
que a maioria das correlações consegue, e o efeito é maior justamente nas transportadoras
mais fracas: os Correios saem de 17,0% para **34,5%** de atraso em chuva de 20 mm ou mais,
enquanto a Entrega Própria vai de 8,8% para 20,7%.

### Insight 3 — A Black Friday aparece no faturamento, e o Natal aparece no atraso

28/11 (Black Friday) é o maior dia do ano: **142 pedidos e R$ 51.657,35**, contra uma média
de 18,2 pedidos por dia comum — 7,8× o movimento normal. Novembro e dezembro juntos valem
R$ 816.418,80, 24,8% da receita do ano.

A conta chega depois. O percentual de atraso sobe de uma faixa de 9,3% a 18,8% nos outros
meses para **22,8% em novembro e 24,4% em dezembro**, e a nota média cai de 4,25 (agosto)
para 3,90 (dezembro). Nos dias mais tensos o número é pior ainda: 29/11 teve 41,5% de atraso
e 25/12 teve 50,0%.

Mas o volume sozinho explica pouco. Dias com menos de 15 pedidos têm 14,6% de atraso e dias
com 25 a 39 pedidos têm 20,6% — o gradiente existe, porém é bem menor que o salto de
novembro/dezembro. O que o pico faz é **somar-se** à chuva de verão: é a combinação, não o
volume isolado.

Os feriados confirmam a leitura em escala menor: 21,93 pedidos por dia de feriado contra
18,23 nos dias comuns (+20%), com atraso médio de 1,12 dia contra 0,71 (+58%). O atraso
cresce mais que o movimento.

### Recomendação de negócio

**Prometer prazo em função da previsão de chuva, e tirar os Correios da chuva forte.**

A promessa hoje é fixa por região e sistematicamente otimista: o Norte promete 11,48 dias e
entrega em 12,86; o Sudeste promete 3,83 e entrega em 4,46. Três ações, em ordem de retorno
sobre esforço:

1. **Prazo dinâmico.** Somar 1 dia ao `prazo_estimado_dias` quando a previsão de
   `chuva_3d_mm` passar de 20 mm. Isso cobre o atraso médio observado nessas faixas
   (1,21 e 1,93 dia) e não custa nada além de uma chamada de API. Como "atraso" é a
   diferença entre o prometido e o realizado, uma promessa honesta elimina a maior parte do
   problema sem mudar um caminhão de lugar.
2. **Roteirizar por clima.** Nos dias de chuva forte, mover o volume dos Correios no Norte e
   no Nordeste para Jadlog ou Entrega Própria. Os Correios atrasam 34,5% nesses dias contra
   20,7% da Entrega Própria; são 653 itens/ano só na faixa 20+ mm.
3. **Reforçar nov/dez.** A capacidade extra tem que entrar antes da Black Friday, não
   depois, porque o atraso de 28/11 vira nota baixa e devolução em dezembro.

Alvo: derrubar o atraso de 16,27% para abaixo de 10%, o que recupera a maior parte dos
R$ 43.548 em devoluções excedentes e devolve a nota média à faixa de 4,25 que a operação já
demonstrou alcançar em julho e agosto.

### Uma leitura que descartamos

O `centro_distribuicao` **não** é uma variável independente: CD-NORTE tem exatamente os
mesmos 385 itens da região Norte, CD-SUDESTE os mesmos 5.444 do Sudeste, e assim por diante.
A correspondência é 1:1 em todos os cinco. Apresentar "o CD-NORTE é o gargalo" seria
apresentar "o Norte é o gargalo" com outro nome, e sugeriria uma ação errada — trocar o CD
em vez de tratar a distância e o clima.

## Visualizações Criadas

Dashboard gerado por `aws-lab/scripts/dashboard_views.py` em
`aws-lab/scripts/dashboard-views.html`. O HTML carrega as 10.000 linhas embutidas e pesa
2,8 MB, então não vai versionado — segue a mesma regra que o `.gitignore` do template já
aplica ao `dashboard.html`. Para reproduzir: `python3 aws-lab/scripts/dashboard_views.py --abrir`
(biblioteca padrão, sem dependências). Os prints estão em `evidencias/`.

**Filtro interativo:** três controles — região (múltipla), categoria (múltipla) e intervalo
de meses — que recalculam **todos os sete gráficos e os seis Big Numbers** a cada mudança.
O print `02-dashboard-filtro-sudeste-nov-dez.png` mostra o filtro Sudeste + nov/dez aplicado:
1.562 itens, atraso de 23,9% contra os 14,4% do Sudeste no ano inteiro, e nota de 3,91
contra 4,14. É o Insight 3 visível em dois cliques.

| # | Gráfico | View que alimenta | O que mostra | Decisão que apoia |
|:-:|---|---|---|---|
| 0 | Stat tiles (6) | `vw_kpis` | Receita, pedidos, ticket, % atrasados, nota, % cancelado+devolvido | Leitura de abertura da diretoria |
| 1 | Barras + linha, por semana | `vw_serie_diaria` | Receita e pedidos ao longo de 2025 | Quando reforçar a capacidade |
| 2 | Barras | `vw_atraso_nota` | Nota média por faixa de atraso | Priorizar prazo sobre preço |
| 3 | Barras ordenadas | `vw_logistica_estado` | % atrasados por estado (mín. 20 itens) | Onde atacar primeiro |
| 4 | Barras empilhadas | `vw_problemas_categoria` | % cancelado e % devolvido por categoria | Onde revisar anúncio e embalagem |
| 5 | Barras + linha | `vw_atraso_chuva` | % atrasados e atraso médio por faixa de chuva | Prazo dinâmico por previsão |
| 6 | Barras agrupadas | `vw_atraso_chuva_regiao` (bônus) | O mesmo gradiente **dentro** de cada região | Separar efeito da chuva do efeito da geografia |
| 7 | Barras de dois eixos | `vw_feriados` | Pedidos por dia e atraso em feriado vs dia comum | Escala em data especial |

Três decisões de desenho que mudam a leitura:

- O gráfico 6 fica **ao lado** do 5 de propósito. O 5 sozinho autoriza a conclusão errada de
  que chove mais onde atrasa mais; o 6 é o teste que decide entre as duas leituras, e a
  resposta só existe com os dois na mesma tela.
- No gráfico 6, faixas com menos de 15 itens ficam vazias em vez de desenhar uma barra. O
  Centro-Oeste tem 18 itens na faixa de chuva muito forte, e uma barra ali tem a mesma altura
  visual de uma com 2.935 itens enquanto vale muito menos.
- As faixas levam prefixo `1)`..`4)` porque o Superset ordena rótulo alfabeticamente; sem o
  prefixo, "sem chuva" apareceria depois de "muito forte" e o gradiente sumiria.

**Sobre a ferramenta.** O dashboard foi montado no **Superset 3.1.3** rodando na EC2 do
`terraform apply`, lendo as views pelo Athena: 11 gráficos (4 Big Numbers, 1 linha, 6 barras,
uma delas empilhada e outra agrupada por região) e **3 filtros nativos** — região, faixa de
chuva e categoria. O print `06-superset-filtro-sudeste.png` mostra o filtro de região em uso:
o gráfico de estados passa a listar só MG, SP e RJ e o gráfico bônus mostra só a série do
Sudeste, com o gradiente de 10,6% a 33,2% isolado.

Mantivemos também o **Plano B local** (`dashboard_views.py`), que replica os mesmos gráficos
e um filtro equivalente sem depender da AWS. Ele foi o que permitiu fechar a análise antes de
abrir a sessão do Learner Lab, e continua útil porque a sessão expira em 4 horas enquanto o
relatório não expira. O `dashboard_local.py` do template desenha 3 gráficos fixos e não tem
filtro; o nosso manda as linhas para o navegador e agrega em JavaScript a cada mudança.

Ele foi redesenhado numa segunda passada, e três decisões vieram de regras de visualização,
não de gosto:

- **Nenhum gráfico tem dois eixos Y.** A primeira versão tinha três — receita com pedidos,
  percentual de atraso com dias de atraso, movimento com atraso no feriado. Duas escalas num
  plano só inventam uma correlação que não está no dado, porque o alinhamento entre elas é
  arbitrário. A segunda medida foi para o tooltip e para a tabela, e o gráfico do feriado
  virou dois.
- **Toda carta tem tabela.** Três dos cinco tons da paleta ficam abaixo de 3:1 de contraste
  contra a superfície clara, e a regra nesse caso é oferecer o valor por outro canal. O botão
  *Tabela* troca o gráfico pelos números, que é também o que torna o dashboard legível para
  quem não distingue as cores.
- **A paleta foi medida, não escolhida a olho.** Os cinco tons passam no teste de separação
  para daltonismo na lista de pares adjacentes (pior par ΔE 9,1 em protanopia, piso 8) e no
  piso de visão normal (pior par ΔE 19,6, piso 15). A cor segue a entidade: a região Sudeste
  tem o mesmo tom antes e depois de qualquer filtro.

## Lições Aprendidas

**O denominador é a decisão de modelagem, não um detalhe.** A `vw_kpis` tem seis métricas com
quatro denominadores diferentes na mesma linha: receita e ticket sobre os entregues, o
percentual de atraso sobre os entregues, a nota sobre os entregues **que avaliaram**, e o
percentual de cancelado+devolvido sobre os 10.000 itens. Por isso o filtro de status vai
dentro de cada agregação, e não no `WHERE`: um `WHERE status = 'entregue'` no topo daria um
percentual de cancelamento igual a zero, e o número sairia bonito e errado.

**Conferir o dado antes de escrever a consulta economiza a consulta errada.** Auditamos a
base antes de escrever qualquer view, e foi assim que descobrimos que itens `devolvido`
**têm** `atraso_dias` preenchido (408 deles) e quase sempre nota (372) — ao contrário dos
`cancelado`, que não têm nada. Quem assume que "só entregue tem entrega" deixa 408 itens
entrarem sem querer e muda a nota média e o percentual de atraso. A mesma auditoria mostrou
que `atraso_dias = prazo_real - prazo_estimado` em 100% das linhas e que não existe atraso
negativo, o que validou as faixas antes do primeiro `CREATE VIEW`.

**Correlação exige procurar o confundidor antes de apresentar, não depois.** A relação entre
chuva e atraso tinha duas explicações alternativas óbvias — região e pico de vendas — e as
duas têm uma consulta de dez linhas que as testa. Levar o gráfico para a diretoria sem rodar
essas duas consultas teria sido apresentar uma recomendação de R$ 43 mil apoiada em algo que
poderia ser só geografia. Testar custou meia hora, e o resultado é mais forte: o efeito
sobrevive. O inverso também vale — o `centro_distribuicao` **não** sobreviveu ao teste, e
teria rendido um slide convincente e inútil.

**Replicação não é execução — e desta vez deu para provar as duas coisas.** A análise foi
fechada primeiro numa replicação das views em DuckDB sobre os mesmos CSVs, porque a sessão do
Learner Lab expira em 4 horas e não havia uma ativa. Escrevemos no relatório que aquilo era
replicação e não execução, porque só o Athena prova o Athena. Depois a sessão foi aberta, as
**9 views foram criadas no Athena sem um único erro de sintaxe** e cada número foi reconsultado
lá: `vw_kpis` devolveu 3297891.59 / 6706 / 491.78 / 16.27 / 4.11 / 7.56, as quatro faixas de
atraso devolveram 4,39 / 3,59 / 2,35 / 1,24, e as vinte linhas da view bônus bateram uma a uma.
A replicação estava certa — **mas isso só se sabe depois de executar**, e era igualmente
possível que não estivesse. A regra que sobrou é a mesma que o grupo levou do Terraform em
outra disciplina: ferramenta que responde "ok" sem tocar no alvo não é verificação, e um
resultado plausível não é um resultado conferido.

**Sobre trabalho em equipe.** Dividir por missão (SQL, dashboard, relatório) funcionou melhor
que dividir por arquivo, porque quem escreveu a view sabia qual gráfico ela alimentava e
pôde nomear as colunas pensando no eixo do gráfico.

## Referências

**Dados**
- Base da disciplina: `aula-14-visualizacao-conclusao/aws-lab/data/pedidos_mercadofacil_tratado.csv`
- Chuva diária 2025: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- Feriados nacionais 2025: [BrasilAPI — Feriados Nacionais](https://brasilapi.com.br/docs#tag/Feriados-Nacionais)

**Documentação**
- [Trino / Athena — funções de data e agregação](https://trino.io/docs/current/functions/datetime.html)
- [Amazon Athena — CREATE VIEW](https://docs.aws.amazon.com/athena/latest/ug/create-view.html)
- [AWS Glue Data Catalog — tabelas sobre CSV](https://docs.aws.amazon.com/glue/latest/dg/tables-described.html)
- [Apache Superset — Creating Charts and Dashboards](https://superset.apache.org/docs/using-superset/creating-your-first-dashboard)
- [Chart.js 4.4](https://www.chartjs.org/docs/4.4.1/)
- [DuckDB — read_csv](https://duckdb.org/docs/data/csv/overview.html)

**Material da disciplina**
- `aula-14-visualizacao-conclusao/README.md` e `Aula_14_Visualizacao_e_Conclusao_do_Projeto.md`
- Aulas 12 (ingestão e pré-processamento) e 13 (análise e modelos), do mesmo projeto MercadoFácil

**Ferramentas de IA**
- Claude (Claude Code) na escrita das views, do gerador do dashboard e deste relatório. Todas
  as consultas foram executadas e conferidas; os números do relatório saem da execução, não
  do modelo. As duas checagens de confundidor da seção "Insight 2" foram rodadas justamente
  para não aceitar a primeira conclusão plausível.

## Checklist de Entregáveis

- [x] Pelo menos uma visualização/dashboard interativo foi criado
      (Zeppelin ou Superset)
- [x] O dashboard/visualização foi conectado aos dados processados nas
      etapas anteriores (Aulas 12 e 13) ou à base tratada fornecida na
      Aula 14 (`pedidos_mercadofacil_tratado.csv`)
- [x] A apresentação final do projeto está pronta
- [x] Print(s) ou link de acesso ao dashboard foram anexados a esta PR
      (comentário ou pasta `evidencias/`, à escolha do grupo)

## Evidências

| Arquivo | O que mostra |
|---|---|
| `evidencias/05-superset-dashboard.png` | **Dashboard no Superset**: 4 Big Numbers, 7 gráficos e os 3 filtros nativos |
| `evidencias/06-superset-filtro-sudeste.png` | O mesmo dashboard com o filtro nativo de região em Sudeste |
| `evidencias/03-athena-validacao.txt` | Consultas de validação no Athena, com o `QueryExecutionId` de cada uma |
| `evidencias/04-athena-views.txt` | `SELECT` de cada view no Athena — a fonte dos números deste relatório |
| `evidencias/07-terraform-apply-destroy.txt` | `Apply complete! Resources: 8 added` e `Destroy complete! Resources: 8 destroyed` |
| `evidencias/01-dashboard-completo.png` | Plano B local (8 gráficos, 6 tiles), sem filtro |
| `evidencias/02-dashboard-filtro-sudeste-nov-dez.png` | Plano B local com filtro Sudeste + nov/dez |
| `aws-lab/sql/03_views_atividade.sql` | As 6 views pedidas e a view bônus |
| `aws-lab/scripts/dashboard_views.py` | Gerador do dashboard (biblioteca padrão) |
| `APRESENTACAO.md` | Roteiro do pitch de 8 minutos |

**Conferência dos números.** Os números deste relatório foram consultados no Athena, e os
mesmos valores aparecem nos Big Numbers do Superset no print: R$ 3,3 M de receita, ticket de
491,78, 16,27% de atraso e nota 4,11. A validação da carga também passou: 10.000 linhas,
7.255 pedidos, período de 2025-01-01 a 2025-12-31, e o JOIN com a chuva fecha em 10.000 itens
com **0 sem par**.

**Encerramento da infra.** `Destroy complete! Resources: 8 destroyed`, e o `terraform state
list` depois do destroy voltou **vazio** — que é a verificação que vale, porque o código de
saída de um pipeline é o do último comando e já nos enganou antes. Nada ficou rodando na
conta do Learner Lab.
