# Pitch final — MercadoFácil (8 minutos, 3 apresentadores)

**Material de apoio:** `aws-lab/scripts/dashboard-views.html` aberto em tela cheia.
Quem fala a parte 2 e 3 opera o mouse na sua vez — não fica um só mexendo.

## Divisão

| Bloco | Quem | Tempo | Papel |
|---|---|:--:|---|
| 1. Problema e arquitetura | **Daniel** | 3 min | abre o caso e explica como o dado chega |
| 2. O atraso custa dinheiro | **José** | 2 min | nota, devolução e a conta de R$ 43,5 mil |
| 3. A chuva e a prova do confundidor | **Matheus** | 2 min | o gráfico bônus, o filtro ao vivo e a recomendação |
| 4. Lições | os três | 1 min | uma lição cada, na ordem Daniel → José → Matheus |

Cada um encerra o seu bloco com a frase de passagem marcada. Sem "agora o fulano vai falar
sobre": a frase já entrega o assunto.

---

# Bloco 1 — DANIEL (3 min)

## O problema (1 min)
Dashboard aberto, tiles no topo.

> "A MercadoFácil faturou R$ 3,3 milhões em 2025 e perdeu R$ 280 mil em cancelamento e
> devolução. Um em cada seis itens entregues chegou atrasado — 16,3%. A diretoria pediu três
> respostas: onde atrasa, por que atrasa, e quanto custa."

Aponta dois tiles, não seis: **16,3% de atraso** e **nota 4,11**.

## A arquitetura (2 min)

```
CSV (S3) ──> Glue Data Catalog ──> Athena (views gold) ──> Superset
   │         pedidos, chuva_diaria,    6 views + 1 bônus
   │         feriados
   └── tudo criado por 1 `terraform apply`
```

Uma frase por camada:

> "O Glue registra o schema com os tipos certos — `data_pedido` como date, `atraso_dias` como
> int. É isso que deixa o Athena fazer média e comparar data sem converter nada na consulta."

> "Nenhum gráfico lê a tabela crua. Cada gráfico lê uma view, e a regra de negócio mora na
> view: receita é a soma dos entregues, atrasado é `atraso_dias > 0`. Se a regra muda, muda
> num lugar só e todos os gráficos acompanham."

> "Os dados de apoio vêm de API pública — chuva do Open-Meteo e feriados da BrasilAPI,
> cruzados por cidade e dia. É o que permite perguntar *por quê*, e não só *quanto*."

**Passagem para o José:**
> "Com esse pipeline no ar, a primeira pergunta que o dado responde é se atraso é um problema
> de experiência ou de caixa."

---

# Bloco 2 — JOSÉ (2 min)

Assume o mouse. Vai no gráfico **A nota cai com o atraso**.

> "4,39 no prazo. 1,24 acima de oito dias. Três pontos de nota perdidos."

Vai para o gráfico de **cancelamento e devolução**, ou clica em **Tabela** nele.

> "A nota é o sintoma. A conta é a devolução: 3,03% nos itens entregues no prazo contra 9,94%
> nos atrasados, e 16,2% acima de oito dias."

> "Dos 1.670 itens atrasados, 166 foram devolvidos. Na taxa do prazo seriam 50. São **115
> devoluções por ano que não aconteceriam**, e ao ticket médio de devolução de R$ 377,47 isso
> vale **R$ 43,5 mil** — sem contar frete reverso nem o cliente que não volta."

Se sobrar tempo, mostra a tabela do gráfico de categoria:
> "E não é uma categoria específica: a amplitude entre categorias é de 1,8 ponto percentual.
> O problema é logístico, não de catálogo."

**Passagem para o Matheus:**
> "Sabendo que custa R$ 43 mil, a pergunta vira por que atrasa. E aí a gente quase comprou uma
> resposta errada."

---

# Bloco 3 — MATHEUS (2 min)

Assume o mouse. Gráfico **A chuva explica o atraso?**

> "12,8% de atraso sem chuva, 31,5% na chuva muito forte. Parece fechado. Mas antes de levar
> isso para a diretoria, a gente tinha duas explicações concorrentes."

Vai para o gráfico **O efeito sobrevive dentro de cada região** — *este é o momento da
apresentação, fale devagar*.

> "A primeira: chove muito no Norte, e o Norte é longe do centro de distribuição. Então a
> gente estratificou. Dentro do Sudeste, onde temos 5.444 itens e o dado é mais firme, vai de
> **10,6% a 33,2%**. O gradiente continua lá dentro."

> "A segunda: o pico de vendas de novembro e dezembro, que junta volume com chuva de verão.
> Tirando novembro e dezembro: 10,8% a 27,4%. Só novembro e dezembro: 19,6% a 37,4%. Aparece
> dos dois lados."

> "**O efeito sobrevive aos dois.** Não é prova de causalidade — falta trânsito, estado da via
> e efetivo da transportadora no dia — mas não é a região, e não é a Black Friday."

**Filtro ao vivo.** Seleciona Região = Sudeste e os meses 2025-11 a 2025-12.

> "Mesmo dashboard, dois cliques: 14,4% de atraso viram 23,9%, e a nota cai de 4,14 para 3,91.
> O pico e a chuva se somam."

**Recomendação.**
> "Somar um dia ao prazo prometido quando a previsão de chuva passar de 20 mm, e tirar os
> Correios da chuva forte no Norte e no Nordeste — eles vão de 17% a 34,5% de atraso na chuva,
> enquanto a Entrega Própria vai de 8,8% a 20,7%. Atraso é a diferença entre o prometido e o
> entregue; dá para atacar os dois lados, e um deles é só uma chamada de API."

---

# Bloco 4 — OS TRÊS (1 min, ~20 s cada)

**DANIEL:**
> "O denominador é a modelagem, não um detalhe. A view de KPIs tem seis métricas e quatro
> denominadores diferentes na mesma linha. Um `WHERE status = 'entregue'` no topo zeraria o
> percentual de cancelamento — e o número sairia bonito."

**JOSÉ:**
> "Auditar antes de consultar. A gente descobriu que item devolvido tem `atraso_dias`
> preenchido, ao contrário do cancelado. Quem supõe que só entregue tem entrega contamina a
> nota média com 408 itens."

**MATHEUS:**
> "Procurar o confundidor antes de apresentar. O centro de distribuição não sobreviveu ao
> mesmo teste que a chuva sobreviveu: é 1 para 1 com a região nos cinco casos. Teria rendido
> um slide convincente e inútil."

**MATHEUS fecha:**
> "A maior parte do trabalho não foi construir o pipeline. Foi desconfiar do primeiro gráfico
> que deu certo."

---

# Arguição — quem responde o quê

Responde quem apresentou o bloco. Se a pergunta não for de ninguém, **Daniel** assume.

### Para o DANIEL (pipeline e modelagem)

| Pergunta | Resposta |
|---|---|
| Por que Athena e não Spark? | 10 mil linhas e pergunta ad-hoc. Athena cobra por dado lido e não tem cluster para manter. |
| Por que a nota média não entra na KPI com todos os itens? | Cancelado não tem nota. Incluir no denominador mediria quem avaliou, não a satisfação. |
| Por que views e não consulta direta no gráfico? | A regra de negócio fica num lugar só. Muda a definição de "atrasado" e os oito gráficos acompanham. |
| Vocês rodaram mesmo na AWS? | Sim. `apply` com 8 recursos, as 9 views criadas no Athena sem erro de sintaxe, cada `QueryExecutionId` está em `evidencias/`, e `destroy` com `state list` vazio no fim. |

### Para o JOSÉ (números e qualidade do dado)

| Pergunta | Resposta |
|---|---|
| De onde sai o R$ 43,5 mil? | 1.670 itens atrasados, 166 devolvidos. Na taxa do prazo, 3,03%, seriam 50,6. A diferença de 115 itens vezes o ticket médio de devolução de R$ 377,47. |
| O dado tinha problema de qualidade? | Nesta base, não: 10.000 linhas, nenhum `item_id` duplicado, nenhuma data inválida e `atraso_dias = prazo_real − prazo_estimado` em 100% das linhas. A pegadinha era o devolvido ter atraso preenchido. |
| Por que o gráfico de receita não mostra os pedidos junto? | Porque seriam dois eixos Y, e duas escalas num plano só inventam uma correlação que não está no dado. Os pedidos estão no tooltip e na tabela. |

### Para o MATHEUS (causalidade e visualização)

| Pergunta | Resposta |
|---|---|
| Isso prova que a chuva causa o atraso? | Não. Prova que os dois confundidores óbvios não explicam. Faltam trânsito, estado da via e efetivo da transportadora. |
| Por que `chuva_3d_mm` e não `chuva_mm`? | É a janela da coleta e da primeira perna do frete: o dia do pedido mais os dois seguintes. A chuva do dia só não alcança a entrega. |
| As faixas de chuva não são arbitrárias? | São as do enunciado, fechadas à esquerda e abertas à direita, para 5 e 20 mm caírem numa faixa só. O gradiente é monotônico em qualquer corte razoável. |
| Por que toda carta tem botão "Tabela"? | Três dos cinco tons ficam abaixo de 3:1 de contraste contra o fundo claro. A regra nesse caso é dar o valor por outro canal — e serve para quem não distingue as cores. |

---

# Checagem de 2 minutos antes de começar

1. `python3 aws-lab/scripts/dashboard_views.py --abrir` — o dashboard é local, não depende de
   internet nem da AWS (só o Chart.js vem de CDN, então confira se os gráficos desenharam).
2. Clique em **Limpar** para zerar qualquer filtro de teste.
3. Confira os tiles: R$ 3.297.892 · 6.706 · R$ 492 · 16,3% · 4,11 · 7,6%. Se estiver diferente,
   tem filtro ligado.
4. Decida o tema (botão **Tema**) conforme o projetor — claro costuma ler melhor em sala com luz.
