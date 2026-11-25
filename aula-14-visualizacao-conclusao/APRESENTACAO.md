# Pitch final — MercadoFácil (8 minutos)

**Grupo:** José Henrique Teixeira Luiz (3225002) · Daniel Tavares (6325032) · Leandro Duarte (6325072)
**Material de apoio:** `aws-lab/scripts/dashboard-views.html` aberto no navegador, em tela cheia.

---

## 1 min — O problema

> "A MercadoFácil faturou R$ 3,3 milhões em 2025 e perdeu R$ 280 mil em cancelamento e
> devolução. Um em cada seis itens entregues chegou atrasado. A diretoria nos pediu três
> respostas: **onde** atrasa, **por que** atrasa, e **quanto isso custa**."

Mostrar os Big Numbers no topo do dashboard enquanto fala. Não ler os seis — apontar dois:
**16,3% de atraso** e **nota 4,11**.

Fechar com a pergunta que organiza o resto: *"atraso é um problema de experiência ou de
caixa?"*

---

## 2 min — A arquitetura

```
CSV (S3) ──> Glue Data Catalog ──> Athena (views gold) ──> Superset / dashboard
   │         pedidos, chuva_diaria,     6 views + 1 bônus
   │         feriados
   └── tudo criado por 1 `terraform apply`
```

Três pontos, um por camada:

1. **S3 + Glue.** O CSV fica no S3; o Glue registra o schema com os tipos certos
   (`data_pedido` como `date`, `atraso_dias` como `int`), e é isso que permite o Athena
   fazer média e comparação de data sem converter nada na consulta.
2. **Athena é a camada gold.** Nenhum gráfico lê a tabela crua. Cada gráfico lê uma view,
   e a regra de negócio vive na view — "receita é a soma dos entregues", "atrasado é
   `atraso_dias > 0`". Se a regra muda, muda em um lugar só e todos os gráficos acompanham.
3. **Os dados de apoio vêm de API pública.** Chuva do Open-Meteo e feriados da BrasilAPI,
   cruzados por cidade e dia. É o que permite perguntar *por que*, e não só *quanto*.

Se perguntarem por que Athena e não Spark: o volume é de 10 mil linhas e a pergunta é
analítica e ad-hoc. Athena cobra por dado lido e não tem cluster para manter.

---

## 4 min — Demonstração ao vivo

**Gráfico 1 — a nota cai com o atraso (40 s).**
"4,39 no prazo, 1,24 acima de oito dias. Três pontos de nota."

**O gráfico que vira dinheiro (50 s).**
"A nota é o sintoma. A conta é a devolução: 3,03% no prazo contra 9,94% nos atrasados.
São 115 devoluções por ano que não aconteceriam, **R$ 43,5 mil**."

**Gráfico da chuva (60 s).**
"12,8% sem chuva, 31,5% na chuva muito forte. Mas antes de vender isso como causa, a gente
tinha duas explicações concorrentes."

**Gráfico da chuva por região — o bônus (70 s).** *Este é o momento do pitch.*
"A primeira era: chove muito no Norte, e o Norte é longe. Então estratificamos. Dentro do
Sudeste, que é onde temos 5.444 itens, vai de 10,6% a 33,2%. A segunda era o pico de vendas.
Tirando novembro e dezembro: 10,8% a 27,4%. Só novembro e dezembro: 19,6% a 37,4%.
O efeito sobrevive aos dois. Não é prova de causalidade — falta trânsito e efetivo — mas não
é a região, e não é a Black Friday."

**Filtro ao vivo (40 s).**
Selecionar Sudeste + nov/dez. "Mesmo dashboard, dois cliques: 14,4% de atraso viram 23,9%,
a nota cai de 4,14 para 3,91. O pico e a chuva de verão se somam."

**A recomendação (40 s).**
"Somar um dia ao prazo prometido quando a previsão passar de 20 mm, e tirar os Correios da
chuva forte no Norte e no Nordeste — eles vão de 17% a 34,5% de atraso na chuva, enquanto a
Entrega Própria vai de 8,8% a 20,7%. Atraso é a diferença entre o prometido e o entregue.
Dá para atacar os dois lados, e um deles é só uma chamada de API."

---

## 1 min — Lições aprendidas

1. **O denominador é a modelagem.** A view de KPIs tem seis métricas e quatro denominadores.
   Um `WHERE status = 'entregue'` no topo zeraria o percentual de cancelamento — e o número
   sairia bonito.
2. **Auditar antes de consultar.** Descobrimos que item devolvido tem `atraso_dias`
   preenchido. Quem supõe que só entregue tem entrega contamina a nota média com 408 itens.
3. **Procurar o confundidor antes de apresentar.** Duas consultas de dez linhas separaram
   "a chuva atrasa" de "chove onde já atrasava". O `centro_distribuicao` não sobreviveu ao
   mesmo teste — é 1:1 com a região — e teria rendido um slide convincente e inútil.

Fechamento: *"A maior parte do trabalho não foi construir o pipeline. Foi desconfiar do
primeiro gráfico que deu certo."*

---

## Perguntas prováveis da banca

| Pergunta | Resposta curta |
|---|---|
| Por que `chuva_3d_mm` e não `chuva_mm`? | É a janela da coleta e da primeira perna do frete: a chuva do dia do pedido mais os dois seguintes. A chuva do dia só não alcança a entrega. |
| Essas faixas de chuva não são arbitrárias? | São as do enunciado, fechadas à esquerda e abertas à direita para 5 e 20 mm caírem numa faixa só. O gradiente é monotônico em qualquer corte razoável. |
| Isso prova que a chuva causa o atraso? | Não. Prova que os dois confundidores óbvios não explicam. Faltam trânsito, estado da via e efetivo da transportadora no dia. |
| Por que a nota média não entra na KPI geral com todos os itens? | Cancelado não tem nota. Incluir no denominador mediria quem avaliou, não a satisfação. |
| Por que os números não vêm de um print do Athena? | A sessão do Learner Lab expira em 4 horas. As views estão em sintaxe Trino e foram replicadas em DuckDB sobre os mesmos CSVs. Replicação não é execução, e o relatório diz isso. |
| Por que o CD não entra na análise? | Porque é 1:1 com a região nos cinco casos. Não é informação nova. |
