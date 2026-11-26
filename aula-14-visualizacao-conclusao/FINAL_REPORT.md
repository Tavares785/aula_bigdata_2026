# Relatório Final do Projeto de Big Data

**Projeto:** MercadoFácil — Visualização e Conclusão (Aula 14)  
**Aluno:** Emar Cristian Silva Teruo Ito  
**RA:** 6325192  
**Data:** 25/11/2026

## Resumo dos Resultados

O objetivo da análise é apoiar decisões da MercadoFácil sobre desempenho comercial, atrasos logísticos, avaliações de clientes e possíveis fatores relacionados às entregas. Para esta etapa, utilizamos a base tratada de 2025 disponibilizada no material da Aula 14, que contém 10.000 linhas de itens de pedidos. Os indicadores abaixo são desta base e **não devem ser confundidos com os resultados da camada Silver/Gold reproduzida na Aula 13**.

No painel geral, o valor associado aos itens entregues foi de **R$ 3.297.981,59**, com **6.706 pedidos entregues distintos**. A proporção de **itens entregues com atraso foi de 16,3%**, e a **nota média foi de 4,11**. Esses indicadores foram observados no dashboard HTML local; o valor monetário representa soma de itens entregues, não receita líquida contábil.

A filtragem por **Centro-Oeste / janeiro de 2025** apresentou **18 pedidos entregues**, **R$ 7.314,02** em itens entregues, **11,5%** de itens atrasados e **nota média de 4,36**. Trata-se de um recorte menor, que não permite concluir, isoladamente, que essa região apresenta desempenho superior ao total em todo o período.

**Três observações numéricas e recomendações:**

1. **Escala comercial:** o painel geral reúne R$ 3.297.981,59 em itens entregues e 6.706 pedidos distintos. Recomenda-se acompanhar a evolução mensal e a composição por categoria para dimensionar capacidade e estoque em períodos sazonais.
2. **Atrasos:** 16,3% dos itens entregues aparecem como atrasados no painel geral. Recomenda-se investigar as faixas de atraso por região e transportadora, priorizando grupos com volume relevante e acompanhando o percentual de itens atrasados após intervenções.
3. **Recorte operacional:** no Centro-Oeste em janeiro, foram 18 pedidos, com 11,5% dos itens entregues atrasados e nota média de 4,36, frente à nota média geral de 4,11. A diferença é apenas descritiva e deve ser interpretada com cautela por envolver bases e volumes distintos.

O dashboard também exibe comparações entre chuva acumulada em três dias e atrasos, além de cancelamentos e devoluções por categoria. **Essas relações são observacionais e não provam causalidade**. Não foi quantificado, nesta etapa, um efeito de feriados, Black Friday ou Natal, nem executada uma análise causal desses fatores.

## Visualizações Criadas

Foi gerado e aberto no navegador um **dashboard HTML local com Chart.js**, a partir de `aws-lab/data/pedidos_mercadofacil_tratado.csv`, usando o script `aws-lab/scripts/dashboard_interativo.py`. O painel possui **filtros interativos por região e mês**, que atualizam os indicadores e os seis gráficos. A captura com os filtros aplicados está em `evidencias/dashboard-filtros.png`.

O painel apresenta quatro indicadores (valor de itens entregues, pedidos entregues distintos, percentual de itens atrasados e nota média) e as seguintes visualizações:

1. **Linha — valor de itens entregues por mês:** permite observar sazonalidade e períodos de maior movimento.
2. **Barras — valor por categoria:** apoia a comparação da participação comercial entre categorias.
3. **Barras — atraso médio por região:** permite investigar diferenças logísticas regionais.
4. **Barras — nota média por faixa de atraso:** explora a associação descritiva entre atraso e avaliação.
5. **Barras agrupadas — percentual cancelado e devolvido por categoria:** destaca categorias que merecem investigação operacional.
6. **Barras — atraso médio por faixa de chuva acumulada:** explora uma possível associação, sem atribuir causalidade.

Os gráficos são alimentados por agregações feitas diretamente no CSV tratado; **não estão conectados a views Athena nem ao Apache Superset**. O arquivo `aws-lab/sql/03_views_atividade.sql` contém as seis definições SQL solicitadas na atividade, porém **elas ainda não foram executadas ou validadas no Athena**. Esta é a alternativa local prevista no roteiro do professor e pode não atender integralmente aos critérios de pontuação máxima do Superset.

## Lições Aprendidas

A integração das etapas anteriores mostrou a importância de distinguir linhas de itens e pedidos distintos ao definir indicadores. A análise também reforçou o cuidado com denominadores, dados ausentes e a interpretação de relações que não demonstram causa e efeito.

Nesta aula, a visualização local permitiu comunicar indicadores executivos sem provisionar infraestrutura AWS adicional. A principal limitação é que o painel HTML não demonstra a arquitetura Athena → Superset solicitada como caminho principal; as views SQL permaneceram sem execução no serviço. Como trabalho individual, foi necessário concentrar o escopo em análise, documentação e visualização reproduzível.

Em uma próxima iteração, seria importante validar as seis views no Athena, conectar os datasets ao Superset, usar filtros nativos e registrar evidências de execução e encerramento da infraestrutura. Também seria útil aprofundar a comparação de feriados, sazonalidade e clima com controles por região e volume de pedidos.

## Referências

- Material da disciplina: `aula-14-visualizacao-conclusao/README.md` e `Aula_14_Visualizacao_e_Conclusao_do_Projeto.md`, repositório `Tavares785/aula_bigdata_2026`.
- Base de dados fornecida na atividade: `aws-lab/data/pedidos_mercadofacil_tratado.csv`.
- Dados de apoio distribuídos com a atividade: `aws-lab/data/chuva_diaria.csv` e `aws-lab/data/feriados.csv`.
- Script fornecido pelo professor: `aws-lab/scripts/dashboard_local.py`.
- Implementação local desta entrega: `aws-lab/scripts/dashboard_interativo.py` e `aws-lab/sql/03_views_atividade.sql`.
- Chart.js: https://www.chartjs.org/docs/latest/

## Checklist de Entregáveis

- [x] Pelo menos uma visualização/dashboard interativo foi criado (alternativa local HTML com Chart.js; não Superset/Zeppelin).
- [x] O dashboard/visualização foi conectado à base tratada fornecida na Aula 14 (`pedidos_mercadofacil_tratado.csv`).
- [x] A apresentação final do projeto está pronta.
- [x] Print(s) ou link de acesso ao dashboard foram anexados à entrega (`evidencias/dashboard-filtros.png`).
