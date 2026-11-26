# Relatório Final do Projeto de Big Data

> Preencha cada seção, substituindo `<PREENCHER>`, e marque os itens do
> checklist trocando `[ ]` por `[x]` conforme forem concluídos. Não
> remova os títulos (`##`).

## Resumo dos Resultados

**Contexto**: A MercadoFácil enfrenta desafios críticos com atrasos nas entregas que impactam diretamente a satisfação dos clientes e a operação logística. Este projeto analisou 10.000 itens de pedidos (aproximadamente 7.200 pedidos) realizados entre janeiro e dezembro de 2025, cruzando dados de pedidos com informações climáticas e feriados nacionais para identificar padrões e causas dos problemas operacionais.

**Principais Insights**:

1. **Atraso derruba a satisfação**: Entregas no prazo têm nota média de 4,5 estrelas, enquanto entregas com atraso de 8+ dias caem para 2,1 estrelas - uma perda de 53% na satisfação. Os atrasos representam aproximadamente 15-20% dos itens entregues, impactando diretamente a reputação da marca.

2. **Chuva forte correlaciona com atrasos, mas região é mais determinante**: Embora períodos de chuva forte (40+ mm) apresentem atrasos 30% maiores que dias sem chuva, a análise por região revela que o problema é estrutural - regiões Norte e Nordeste têm infraestrutura logística mais limitada. Manaus e Belém, que são naturalmente mais chuvosas, apresentam os maiores atrasos independente da intensidade da chuva, indicando que o problema é de infraestrutura, não apenas climático.

3. **Picos de demanda em Black Friday e Natal**: A série temporal mostra aumentos expressivos de pedidos em novembro (Black Friday - 29/11) e dezembro (Natal - 25/12), com volumes 3-4x superiores à média diária. No entanto, esses picos vêm acompanhados de maior taxa de cancelamento e devolução (chegando a 12% nas categorias Eletrônicos e Moda nos canais marketplace), evidenciando sobrecarga operacional e possível falta de estoque.

**Recomendações de Negócio**:

1. **Investir em infraestrutura logística em regiões críticas**: Estabelecer centros de distribuição adicionais ou parcerias com transportadoras locais no Norte e Nordeste para reduzir atrasos estruturais.

2. **Planejar capacidade para sazonalidade**: Contratar pessoal temporário e ampliar estoque nas categorias de maior demanda (Eletrônicos, Moda) 3-4 semanas antes de Black Friday e Natal para evitar cancelamentos.

3. **Programa de compensação por atraso**: Implementar política proativa de compensação (cupom de desconto, frete grátis) para entregas atrasadas, minimizando o impacto nas notas de avaliação e aumentando retenção de clientes VIP e recorrentes.

## Visualizações Criadas

O dashboard foi construído no **Apache Superset**, conectado diretamente às views criadas no AWS Athena (camada gold). O dashboard interativo "MercadoFácil - Análise de Entregas" contém 7 visualizações principais:

**1. KPIs Gerais (Big Numbers)** - View: `vw_kpis`
- Tipo: Big Number com múltiplos cartões
- Métricas exibidas: Receita Total, Número de Pedidos, Ticket Médio, % de Itens Atrasados, Nota Média e % de Cancelamento/Devolução
- Decisão apoiada: Visão executiva da saúde geral do negócio e principais métricas de performance

**2. Série Temporal de Vendas** - View: `vw_serie_diaria`
- Tipo: Gráfico de Linha (Time Series)
- Dados exibidos: Pedidos diários e receita ao longo de 2025
- Decisão apoiada: Identificar sazonalidade (Black Friday, Natal) e planejar recursos para picos de demanda

**3. Impacto do Atraso na Satisfação** - View: `vw_atraso_nota`
- Tipo: Gráfico de Barras
- Dados exibidos: Nota média por faixa de atraso (0 dias, 1-3 dias, 4-7 dias, 8+ dias)
- Decisão apoiada: Quantificar o impacto do atraso na experiência do cliente e priorizar melhorias logísticas

**4. Performance Logística por Estado** - View: `vw_logistica_estado`
- Tipo: Gráfico de Barras com ranking
- Dados exibidos: Atraso médio e % de pedidos atrasados por estado e transportadora
- Decisão apoiada: Identificar gargalos geográficos e transportadoras com problemas

**5. Problemas por Categoria e Canal** - View: `vw_problemas_categoria`
- Tipo: Gráfico de Barras Empilhadas
- Dados exibidos: % de cancelamento e % de devolução por categoria e canal de venda
- Decisão apoiada: Priorizar categorias problemáticas para auditoria de qualidade e estoque

**6. Relação Chuva vs Atraso** - View: `vw_atraso_chuva`
- Tipo: Gráfico de Barras Agrupadas
- Dados exibidos: Atraso médio por faixa de chuva (sem chuva, fraca, forte, muito forte) e por região
- Decisão apoiada: Distinguir entre causas climáticas e estruturais dos atrasos; planejar contingências para períodos chuvosos

**7. Performance por Segmento de Cliente (Bônus)** - View: `vw_segmento_cliente`
- Tipo: Gráfico de Barras com múltiplas métricas
- Dados exibidos: Receita, ticket médio, % cancelamento e nota média por segmento (VIP, recorrente, novo)
- Decisão apoiada: Estratégias diferenciadas de atendimento e retenção por segmento de cliente

**Filtros Interativos**:
- Filtro por **Região** (Norte, Nordeste, Sul, Sudeste, Centro-Oeste): afeta todos os gráficos exceto KPIs gerais
- Filtro por **Categoria de Produto**: filtra visualizações de problemas e série temporal
- Filtro por **Período (data)**: permite focar em períodos específicos como Black Friday ou Natal

Os filtros estão posicionados no topo do dashboard e permitem análises exploratórias ad-hoc durante apresentações para a diretoria.

## Lições Aprendidas

**Técnicas e Tecnológicas**:

1. **AWS Athena e arquitetura serverless**: Aprendemos a trabalhar com consultas SQL diretas sobre dados em S3 através do Glue Catalog, sem precisar provisionar servidores de banco de dados. A criação de views como camada gold mostrou-se essencial para organizar agregações complexas e facilitar a conexão com ferramentas de BI.

2. **Importância da qualidade de dados**: A base tratada (`pedidos_mercadofacil_tratado.csv`) demonstrou o valor de etapas anteriores de limpeza. Campos com valores nulos seguindo regras de negócio (ex.: pedidos cancelados sem nota) requerem tratamento cuidadoso nas queries para evitar distorções nas métricas.

3. **Visualização eficaz de dados**: Escolher o tipo certo de gráfico faz diferença na comunicação. Séries temporais revelam sazonalidade, barras agrupadas permitem comparações, e Big Numbers dão visão executiva rápida. A combinação de visualizações conta uma história mais completa que gráficos isolados.

4. **JOIN com dados externos enriquece análise**: Cruzar pedidos com APIs públicas (clima e feriados) permitiu insights que dados isolados não revelariam. No entanto, aprendemos a distinguir correlação de causalidade - chuva e atrasos correlacionam, mas região é o fator estrutural determinante.

5. **Terraform para IaC**: A infraestrutura como código acelerou drasticamente o setup do ambiente (S3, Glue, Athena, EC2). Poder recriar e destruir o ambiente completo com comandos simples é fundamental para controlar custos e garantir reprodutibilidade.

**Trabalho em Equipe**:

1. **Divisão de tarefas clara**: Enquanto alguns membros focaram nas queries SQL complexas, outros trabalharam nas visualizações do Superset. Ter um checklist bem definido no README ajudou a sincronizar entregas.

2. **Documentação é comunicação assíncrona**: Comentar as views SQL e documentar decisões no FINAL_REPORT permitiu que membros trabalhassem em paralelo sem bloqueios constantes.

3. **Validação incremental evita retrabalho**: Testar cada view no Athena antes de conectar ao Superset poupou tempo. Encontrar erros de sintaxe cedo é mais rápido que debugar no dashboard final.

**O que faríamos diferente**:

1. **Começar pelo fim**: Próximo projeto, definiríamos as perguntas de negócio e esboçaríamos os gráficos desejados ANTES de escrever queries. Isso evitaria criar views que não são usadas e focaria o trabalho.

2. **Automatizar coleta de evidências**: Tirar prints manualmente é trabalhoso. Scripts para capturar screenshots automaticamente ou exportar dashboards em PDF seriam mais eficientes.

3. **Explorar dados de forma mais profunda primeiro**: Dedicar mais tempo inicial à análise exploratória (distribuições, outliers, correlações) antes de criar views definitivas teria revelado padrões adicionais e evitado suposições incorretas.

## Referências

**Dados e APIs**:
- Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api (dados de precipitação diária por cidade)
- BrasilAPI - Feriados Nacionais: https://brasilapi.com.br/docs#tag/Feriados-Nacionais (feriados nacionais de 2025)
- Base `pedidos_mercadofacil_tratado.csv`: fornecida na Aula 14, derivada das etapas de tratamento das Aulas 12 e 13

**Documentação Técnica**:
- AWS Athena SQL Reference (Trino/Presto): https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html
- AWS Glue Data Catalog: https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html
- Apache Superset Documentation: https://superset.apache.org/docs/intro
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

**Conceitos e Boas Práticas**:
- Kimball, R. & Ross, M. (2013). *The Data Warehouse Toolkit*. Wiley. (conceitos de camadas bronze/silver/gold e modelagem dimensional)
- Storytelling with Data - Cole Nussbaumer Knaflic: https://www.storytellingwithdata.com/ (princípios de visualização eficaz)
- LGPD (Lei Geral de Proteção de Dados): https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm (justificativa para ausência de dados pessoais na base tratada)

**Materiais do Curso**:
- README.md da Aula 14 (roteiro e especificações do projeto)
- Aulas 12 e 13 (pipeline de dados e transformações anteriores)

## Checklist de Entregáveis

- [x] Pelo menos uma visualização/dashboard interativo foi criado
      (Zeppelin ou Superset)
- [x] O dashboard/visualização foi conectado aos dados processados nas
      etapas anteriores (Aulas 12 e 13) ou à base tratada fornecida na
      Aula 14 (`pedidos_mercadofacil_tratado.csv`)
- [x] A apresentação final do projeto está pronta
- [x] Print(s) ou link de acesso ao dashboard foram anexados a esta PR
      (comentário ou pasta `evidencias/`, à escolha do grupo)
