# Relatório Final do Projeto de Big Data

## Resumo dos Resultados

**Contexto.** A MercadoFácil, e-commerce brasileiro de médio porte, vinha
com entregas atrasadas, avaliações baixas e cancelamentos e devoluções acima
da meta. Montamos um pipeline na AWS (S3, Glue, Athena e Superset) sobre 10.000
itens de pedido de 2025 (6.706 pedidos entregues, receita de R$ 3,30 milhões,
ticket médio de R$ 491,78) para responder onde e por que as entregas atrasam e
quanto isso custa.

**O que os dados mostram.**

1. **O atraso derruba a nota e aumenta a devolução.** A nota média é 4,39 nas
   entregas no prazo, 3,59 com 1 a 3 dias de atraso, 2,35 com 4 a 7 dias e 1,24
   com 8 dias ou mais. Entre os itens entregues ou devolvidos, 9,9% dos
   atrasados foram devolvidos, contra 3,0% dos entregues no prazo. No total,
   16,3% dos itens entregues chegam atrasados.
2. **A chuva está associada ao atraso, mas a região também pesa.** O atraso
   médio sobe de 0,49 dia sem chuva para 1,93 dia com chuva muito forte (acima
   de 40 mm), e a parcela de itens atrasados vai de 12,8% para 31,5%. O padrão
   aparece dentro de cada região (no Sudeste, de 0,38 para 1,99 dia), então a
   chuva não é só um reflexo da região. Mesmo assim, o Norte atrasa mais
   (24,2% de itens atrasados, contra 14,4% no Sudeste). É uma associação
   observada nos dados, não uma prova de causa.
3. **A Black Friday e o fim de ano pressionam a operação.** Na semana da Black
   Friday a média sobe de 17,9 para 41,9 pedidos por dia, com pico de 142
   pedidos entregues em 28/11. O atraso médio passa de cerca de 0,5 dia nos meses comuns
   para 1,24 em novembro e 1,32 em dezembro, e a parcela de itens atrasados vai
   de 9% a 19% de janeiro a outubro para 23% e 24% nos dois últimos meses. A
   transportadora também importa: os Correios atrasam 20,1% dos itens e a
   entrega própria, 11,0%.

**Recomendação.** (a) Reforçar a capacidade logística e antecipar o estoque nos
CDs antes de novembro, porque é aí que o atraso dobra. (b) Revisar prazos e
transportadoras nas regiões Norte e Nordeste, e prever folga de prazo em dias
de chuva forte. (c) Acompanhar o atraso como indicador de nota e de devolução:
cada faixa de atraso custa nota, e um atraso de 4 dias ou mais deixa a nota
abaixo de 2,4. Como análise complementar da Aula 13, um modelo de previsão de
atraso teve poder fraco (AUC de 0,67), o que reforça que o mês e a operação
explicam mais do que o cadastro do cliente ou do produto.

## Visualizações Criadas

As visualizações foram feitas no **Apache Superset** (EC2 na AWS Academy),
ligado ao **Athena** pelo banco `mercadofacil_aula14`. Criamos 7 gráficos, cada
um lendo uma view gold de `aws-lab/sql/03_views_atividade.sql`. O dashboard
**MercadoFácil** foi salvo com 6 deles. O gráfico **Nota média por faixa de
atraso** foi criado, mas não entrou no dashboard salvo, e o filtro nativo por
categoria não chegou a ser gravado; ficam como melhoria. Os gráficos e as
decisões que apoiam:

- **Receita total** (Big Number, `vw_kpis`): mostra o tamanho do negócio
  (R$ 3,30 milhões) e serve de referência para o impacto dos atrasos.
- **Receita diária** (linha, `vw_serie_diaria`): mostra o pico da Black Friday
  e o aumento de novembro e dezembro; apoia o planejamento de capacidade.
- **Receita por categoria** (pizza, `vw_vendas_mensal`): mostra o peso de cada
  categoria na receita; apoia a decisão de onde concentrar estoque e logística.
- **Nota média por faixa de atraso** (barras, `vw_atraso_nota`, criado no
  Superset e fora do dashboard salvo): mostra que a nota cai de 4,39 para 1,24
  conforme o atraso cresce; apoia a meta de prazo.
- **% de itens atrasados por região** (barras, `vw_logistica_estado`): mostra
  onde atrasa mais; apoia a decisão sobre CDs e transportadoras por região.
- **Cancelamento e devolução por categoria** (barras empilhadas,
  `vw_problemas_categoria`): mostra quais categorias e canais têm mais
  problemas; apoia ações de qualidade por categoria.
- **Atraso médio por faixa de chuva** (barras, `vw_atraso_chuva`): mostra a
  associação entre chuva e atraso; apoia a folga de prazo em dias de chuva.

As views também usam as tabelas de apoio de chuva (Open-Meteo) e feriados
(BrasilAPI). Além das seis views pedidas, criamos a `vw_desconto_problemas`,
que mostra que descontos acima de 20% vêm com mais cancelamento (5,8%, contra
cerca de 3,5% nas outras faixas) e valor médio do item menor.

## Lições Aprendidas

- **Técnicas.** O Learner Lab impõe limites que moldam a arquitetura: sem
  roles IAM novas (usamos a LabRole), sem o recurso `aws_s3_bucket` (criamos o
  bucket pela CLI) e credenciais que expiram. O Terraform deixou o ambiente
  reprodutível e fácil de derrubar com um `destroy`.
- **Qualidade dos dados.** A maior parte do esforço da Aula 12 foi limpar o
  dado bruto (datas em três formatos, valores em `R$`, nulos escritos de várias
  formas, categorias truncadas e duplicados). Documentar cada regra e mandar as
  linhas inaproveitáveis para uma quarentena evitou descartes silenciosos.
- **Análise.** Validar as views localmente, com os mesmos CSVs, antes de rodar
  no Athena economizou tempo e crédito, e os números bateram. Na Aula 13 vimos
  que ter um modelo não basta: o desempenho foi modesto e precisou ser
  explicado com honestidade, sem vender mais do que os dados sustentam.
- **Visualização.** No Superset, a edição do dashboard só vale depois do botão
  Save, e um filtro só afeta os gráficos cujo dataset tem a coluna; por isso o
  desenho das views precisa prever o que será filtrado. Não concluímos o filtro
  nem incluímos um dos gráficos a tempo, e o ambiente foi desligado em seguida.
- **O que faríamos diferente.** Padronizar fim de linha e o `.gitignore` desde
  o início, para não acumular alterações irrelevantes, e começar o dashboard
  mais cedo para ter tempo de refinar os gráficos.

## Referências

- Dados: `pedidos_mercadofacil.csv` (Aula 12, dump bruto) e
  `pedidos_mercadofacil_tratado.csv` (Aula 14), fornecidos pelo professor.
- Chuva diária por cidade: Open-Meteo Archive API
  (https://open-meteo.com/en/docs/historical-weather-api).
- Feriados nacionais: BrasilAPI (https://brasilapi.com.br/docs#tag/Feriados-Nacionais).
- Terraform AWS Provider 5.31.0: `aws_glue_job`, `aws_glue_crawler`,
  `aws_glue_catalog_database` e `aws_athena_workgroup`
  (https://registry.terraform.io/providers/hashicorp/aws/5.31.0/docs).
- Documentação do AWS Glue, do Amazon Athena (Trino) e do Apache Superset
  (https://superset.apache.org/docs/intro).
- Apache Spark MLlib, para o modelo de previsão de atraso da Aula 13.
- Roteiros e READMEs das Aulas 12, 13 e 14 do curso de Big Data.

## Checklist de Entregáveis

- [x] Pelo menos uma visualização/dashboard interativo foi criado
      (Zeppelin ou Superset)
- [x] O dashboard/visualização foi conectado aos dados processados nas
      etapas anteriores (Aulas 12 e 13) ou à base tratada fornecida na
      Aula 14 (`pedidos_mercadofacil_tratado.csv`)
- [x] A apresentação final do projeto está pronta
- [x] Print(s) ou link de acesso ao dashboard foram anexados a esta PR
      (comentário ou pasta `evidencias/`, à escolha do grupo)
