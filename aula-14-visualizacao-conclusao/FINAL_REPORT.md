# Relatório Final do Projeto de Big Data

## Resumo dos Resultados

### Contexto

O MercadoFácil opera com 10.000 itens de pedido registrados ao longo de 2025,
distribuídos por cinco regiões do Brasil e oito categorias de produto. A diretoria
precisava entender onde e por que as entregas atrasam, quanto esse atraso custa em
satisfação e devoluções, e como eventos sazonais como Black Friday e Natal pressionam
a operação.

### O que os dados mostram

**Receita e volume:** R$ 3,3 milhões de receita em pedidos entregues, com 6.706
pedidos únicos e ticket médio de R$ 491,78. Novembro (Black Friday) e dezembro (Natal)
concentram os dois maiores meses do ano, com picos que chegam a quase o dobro da média
mensal dos demais meses.

**Atraso e satisfação:** 16,3% dos itens entregues chegaram com atraso. O impacto na
nota é direto e severo — itens entregues no prazo recebem nota média de 4,39/5, enquanto
itens com 8 ou mais dias de atraso caem para 1,24/5. Essa queda de 72% na satisfação é
a principal alavanca de melhoria identificada no projeto.

**Logística regional:** A região Norte concentra o maior atraso médio (1,38 dias),
mais que o dobro do Sudeste (0,62 dias). A diferença reflete cobertura logística menor
e distâncias maiores entre centros de distribuição e destino final.

**Efeito da chuva:** Cruzando os pedidos com dados reais da API Open-Meteo, identificamos
correlação positiva entre chuva acumulada nos três dias seguintes ao pedido e o atraso
médio. Com menos de 5 mm de chuva, o atraso médio é de 0,49 dias. Com mais de 40 mm,
sobe para 1,93 dias — quase quatro vezes mais. Importante: os dados mostram correlação,
não causalidade isolada. Para confirmar causalidade seria necessário um modelo de
regressão controlando região e transportadora simultaneamente.

**Problemas por categoria:** Beleza & Saúde registra o maior percentual de cancelamentos
(~5%). Brinquedos lidera em devoluções (~4,6%). Eletrônicos representa 45% da receita
total (R$ 1,47 mi) e concentra o maior volume absoluto de devoluções.

### Recomendações de negócio

1. **Priorizar logística no Norte:** reduzir o atraso médio nessa região tem impacto
   direto na nota e nas devoluções. Avaliar parceiros regionais ou redistribuir estoque
   para centros de distribuição mais próximos.

2. **Ajustar prazo estimado em períodos de chuva intensa:** adicionar buffer automático
   no prazo prometido ao cliente quando a previsão indica chuva acima de 20 mm nos
   próximos três dias. Evita frustração sem mudar a operação.

3. **Reforçar capacidade antes da Black Friday:** contratar transportadoras adicionais
   em outubro, não em novembro. O pico de volume começa semanas antes do evento e a
   logística não tem tempo de reagir se o reforço for tardio.

---

## Visualizações Criadas

O dashboard foi construído em HTML com Chart.js e gerado pelo script
`aws-lab/scripts/gerar_dashboard_interativo.py`, com todos os dados embutidos
diretamente no arquivo. Não depende de servidor ou conexão com banco de dados para
funcionar — apenas de internet para carregar a biblioteca Chart.js via CDN.

### Filtros interativos

O dashboard possui quatro filtros nativos encadeados que afetam todos os gráficos e
KPIs simultaneamente:

- **Região** (Centro-Oeste, Nordeste, Norte, Sudeste, Sul)
- **Categoria** (Eletrônicos, Moda, Casa e Cozinha, Esporte, Beleza e Saúde, Livros,
  Brinquedos, Pet)
- **Mês** (janeiro a dezembro de 2025)
- **Canal de venda** (app, site, marketplace_parceiro)

### KPIs no topo

Seis indicadores reativos atualizados a cada mudança de filtro: Receita Total,
Itens Entregues, Ticket Médio, Nota Média, % Itens Atrasados e % Devolvidos.

### Gráficos

| # | Tipo | View / Fonte | Pergunta respondida | Decisão que apoia |
|---|---|---|---|---|
| 1 | Linha | `vw_serie_diaria` | Black Friday e Natal aparecem na receita? | Planejamento de capacidade logística |
| 2 | Barras | `vw_atraso_nota` | O atraso derruba a nota do cliente? | Priorização de SLA de entrega |
| 3 | Barras | `vw_logistica_estado` | Qual região atrasa mais? | Escolha de parceiros regionais |
| 4 | Barras | `vw_logistica_estado` | Qual transportadora atrasa mais? | Renegociação ou troca de transportadora |
| 5 | Barras empilhadas | `vw_problemas_categoria` | Quais categorias cancelam e devolvem mais? | Revisão de política de cancelamento por categoria |
| 6 | Barras | `vw_atraso_chuva` | A chuva explica o atraso? | Ajuste dinâmico de prazo estimado |
| 7 | Barras | `vw_serie_diaria` | Qual canal gera mais receita? | Alocação de investimento por canal |
| 8 | Barras | `vw_logistica_estado` | O canal de venda influencia o atraso? | Revisão de SLA por canal |

### Arquivo gerado

`aws-lab/scripts/dashboard_interativo.html` — abre diretamente no navegador sem
instalação adicional.

---

## Lições Aprendidas

### Técnicas

**AWS e infraestrutura como código:** O Terraform mostrou na prática o valor de tratar
infraestrutura como código. Um único `terraform apply` sobe S3, Glue, Athena e Superset;
um `terraform destroy` elimina tudo e zera o custo. Sem isso, o risco de deixar recursos
rodando e consumir créditos do Learner Lab seria alto.

**Athena e o modelo serverless:** Consultar arquivos CSV diretamente no S3 via SQL sem
configurar servidor foi a maior surpresa positiva do projeto. O modelo serverless é
genuinamente diferente — você paga pela consulta, não pela capacidade ociosa.

**Qualidade de dados antes de tudo:** A base já chegou tratada (camada Silver), mas o
processo de validação com `01_validar.sql` mostrou que mesmo dados tratados têm campos
vazios esperados — pedidos cancelados não têm data de entrega nem nota. Tratar isso como
erro seria um equívoco analítico.

**Enriquecimento com fontes externas:** O JOIN com chuva e feriados gerou os insights
mais interessantes do projeto. Dados internos sozinhos respondem "o quê"; dados externos
ajudam a responder "por quê".

**Correlação vs. causalidade:** A análise da chuva gerou uma discussão importante. Os
dados mostram correlação clara, mas atribuir causalidade sem controlar outras variáveis
(região, transportadora, época do ano) seria uma conclusão precipitada.

### Sobre o processo

O maior aprendizado foi a importância de definir as perguntas de negócio antes de
construir o dashboard. Começar pelos gráficos sem saber qual decisão eles precisam
apoiar resulta em visualizações bonitas que ninguém usa. A estrutura da aula — primeiro
as views, depois os gráficos — forçou essa disciplina.

---

## Referências

- **Dados de pedidos:** `aws-lab/data/pedidos_mercadofacil_tratado.csv` — base sintética
  gerada para o projeto integrador da disciplina de Big Data 2026.
- **Dados de chuva:** Open-Meteo Historical Weather API —
  https://open-meteo.com/en/docs/historical-weather-api
- **Feriados nacionais:** BrasilAPI —
  https://brasilapi.com.br/docs#tag/Feriados-Nacionais
- **Visualização:** Chart.js v4.4.3 — https://www.chartjs.org
- **Infraestrutura:** HashiCorp Terraform — https://www.terraform.io
- **Consulta analítica:** AWS Athena — https://aws.amazon.com/athena
- **Catálogo de dados:** AWS Glue — https://aws.amazon.com/glue
- **Dashboard BI:** Apache Superset — https://superset.apache.org
- Knaflic, C. N. (2015). *Storytelling with Data.* Wiley.
- Reis, J., & Housley, M. (2022). *Fundamentals of Data Engineering.* O'Reilly Media.

---

## Checklist de Entregáveis

- [x] Pelo menos uma visualização/dashboard interativo foi criado
      (dashboard_interativo.html com 8 gráficos e 4 filtros encadeados)
- [x] O dashboard/visualização foi conectado aos dados processados nas
      etapas anteriores (Aulas 12 e 13) ou à base tratada fornecida na
      Aula 14 (`pedidos_mercadofacil_tratado.csv`)
- [x] A apresentação final do projeto está pronta
- [x] Print(s) ou link de acesso ao dashboard foram anexados a esta PR
      (comentário ou pasta `evidencias/`, à escolha do grupo)
