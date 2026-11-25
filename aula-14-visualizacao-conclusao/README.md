# Etapa do Projeto - Aula 14: Visualização e Conclusão

## Objetivo

Transformar os dados da **MercadoFácil** em um **dashboard interativo**
que conte uma história para a diretoria, e documentar o resultado no
`FINAL_REPORT.md`. Hoje o grupo não constrói pipeline: parte de uma base
já tratada e foca em **consultar, agregar, visualizar e comunicar**.

> A diretoria quer saber: *onde e por que as entregas atrasam, quanto o
> atraso custa em nota e devoluções, e como a Black Friday e o Natal
> pressionam a operação.*

## Dado fornecido

`aws-lab/data/pedidos_mercadofacil_tratado.csv`: **10.000 linhas** (1 linha =
1 item de pedido, ~7,2 mil pedidos, jan–dez/2025). É a mesma base da Aula 12,
já tratada: tipos corretos, categorias padronizadas, sem duplicados e **sem
dados pessoais** (LGPD). Quem quiser, pode usar a própria camada gold das
Aulas 12 e 13, mas o restante do roteiro assume esta base.

| Grupo | Colunas |
|---|---|
| Pedido | `pedido_id`, `item_id`, `data_pedido`, `status_pedido` (`entregue`, `cancelado`, `devolvido`), `canal` |
| Cliente | `cliente_id`, `cliente_segmento` |
| Destino | `estado`, `regiao`, `cidade` |
| Produto | `categoria`, `sku`, `produto`, `marca`, `custo_unitario` |
| Valores | `preco_unitario`, `quantidade`, `desconto_pct`, `valor_total` |
| Pagamento | `forma_pagamento`, `parcelas` |
| Logística | `transportadora`, `centro_distribuicao`, `prazo_estimado_dias`, `prazo_real_dias`, `atraso_dias`, `data_entrega` |
| Avaliação | `nota_avaliacao` (1 a 5) |

### Dados de apoio (APIs públicas)

Para ficar mais perto do real, a atividade cruza os pedidos com dois dados
**reais de 2025** obtidos de APIs públicas, sem chave:

| Tabela | Fonte | Colunas |
|---|---|---|
| `chuva_diaria` | [Open-Meteo Archive](https://open-meteo.com/en/docs/historical-weather-api) | `cidade`, `dia`, `chuva_mm`, `chuva_3d_mm` (dia do pedido + 2 dias seguintes) |
| `feriados` | [BrasilAPI](https://brasilapi.com.br/docs#tag/Feriados-Nacionais) | `dia`, `nome`, `tipo` |

Os CSVs já estão em `aws-lab/data/`. O script `aws-lab/scripts/buscar_apis.py`
refaz a coleta (precisa de internet). Junte `pedidos` e `chuva_diaria` por
`cidade` e `data_pedido = dia`.

Campos vazios são esperados: pedidos `cancelado` não têm entrega nem nota, e
nem todo cliente avalia.

## Arquitetura da atividade

```
CSV (S3) -> Glue Catalog (pedidos, chuva_diaria, feriados) -> Athena (views gold) -> Superset (dashboard)
        \___________ tudo criado por 1 terraform apply ___________/
```

O Terraform já vem pronto em `aws-lab/infra/`. Ele cria o bucket S3, envia o
CSV, registra as 3 tabelas no Glue, cria o workgroup do Athena e, opcionalmente,
uma EC2 com **Apache Superset** já conectado ao Athena.

## Roteiro (grupo, ~3 h)

### Missão 0 - Preparação (10 min)

1. Inicie o Learner Lab e copie as credenciais (**AWS Details → Show**):
   ```bash
   export AWS_ACCESS_KEY_ID=...  AWS_SECRET_ACCESS_KEY=...  AWS_SESSION_TOKEN=...
   export AWS_DEFAULT_REGION=us-east-1
   aws sts get-caller-identity      # deve responder sem erro
   ```
2. Configure o Terraform:
   ```bash
   cd aws-lab/infra
   cp terraform.tfvars.example terraform.tfvars
   curl -s https://checkip.amazonaws.com        # seu IP -> use IP/32 em meu_ip_cidr
   ```
   Edite `terraform.tfvars`: `bucket_nome` único, `meu_ip_cidr` e
   `superset_senha`. Esse arquivo **não** vai para o Git.

### Missão 1 - Subir o ambiente (15 min)

```bash
terraform init && terraform apply     # confirme com yes
```

Anote os outputs (`athena_workgroup`, `glue_database`, `superset_url`). O
Superset leva cerca de **8 minutos** depois do apply para responder; siga para
a Missão 2 enquanto isso.

### Missão 2 - Athena: dados → camada gold (45 min)

No console do Athena, escolha o **workgroup** do output e o **banco**
`mercadofacil_aula14`.

1. `aws-lab/sql/01_validar.sql`: confira a carga (10.000 linhas), os nulos e se o JOIN com a chuva casa.
2. `aws-lab/sql/02_views_prontas.sql`: crie as 2 views de exemplo.
3. `aws-lab/sql/03_views_atividade.sql`: **crie as 6 views pedidas**
   (`vw_atraso_nota`, `vw_problemas_categoria`, `vw_serie_diaria`, `vw_kpis`,
   `vw_atraso_chuva`, `vw_feriados`), com os nomes de coluna indicados. As duas
   últimas fazem JOIN com as tabelas das APIs.
4. Bônus: uma 5ª view com uma pergunta do próprio grupo.

Salve seus SQLs finais em `aws-lab/sql/` (é o que o professor revisa).

### Missão 3 - Superset: dashboard (60 min)

1. Abra o `superset_url` (usuário `admin`, senha do `terraform.tfvars`). A
   conexão **Athena - MercadoFacil** já está cadastrada.
2. Em **Datasets**, adicione cada view (schema `mercadofacil_aula14`).
3. Crie **no mínimo 6 gráficos**, de tipos variados:

   | Gráfico | View | Pergunta |
   |---|---|---|
   | Big Numbers (receita, ticket, % atrasos, nota) | `vw_kpis` | Como está o negócio? |
   | Linha | `vw_serie_diaria` | Black Friday e Natal aparecem? |
   | Barras | `vw_atraso_nota` | O atraso derruba a nota? |
   | Barras por região/estado | `vw_logistica_estado` | Onde e com quem atrasa mais? |
   | Barras empilhadas | `vw_problemas_categoria` | Quais categorias/canais têm mais cancelamento e devolução? |
   | Barras | `vw_atraso_chuva` | A chuva explica o atraso? E a região, ou os dois? |

4. Monte **um dashboard** com os gráficos e pelo menos **um filtro nativo**
   (ex.: região, categoria ou mês) que afete mais de um gráfico.
5. Todo gráfico precisa de título claro e eixos legíveis.

> **Plano B** se o Superset não subir (veja *Problemas comuns*): rode
> `python3 aws-lab/scripts/dashboard_local.py --abrir` para gerar um dashboard
> HTML a partir do CSV, e tire o print dele. Vale como evidência, mas a nota
> máxima exige o dashboard interativo.

### Missão 4 - Storytelling e relatório (30 min)

1. Escreva 3 insights com número (um deles sobre chuva ou feriado, dizendo se é causa ou só correlação) e uma recomendação de negócio. Estrutura:
   **contexto → o que os dados mostram → o que fazer**.
2. Preencha o `FINAL_REPORT.md` e marque o checklist.
3. Prepare o pitch de **8 min** (1 min problema, 2 min arquitetura, 4 min
   demonstração ao vivo, 1 min lições aprendidas).

### Missão 5 - Encerrar (OBRIGATÓRIO, 5 min)

```bash
cd aws-lab/infra && terraform destroy     # confirme com yes
```

Isso apaga a EC2, o Athena e o bucket. Faça **depois** de tirar os prints.

## O que entregar (PR do grupo)

- `FINAL_REPORT.md` preenchido e checklist marcado;
- `aws-lab/sql/03_views_atividade.sql` com as 6 views (e o bônus);
- prints em `evidencias/` (mascare credenciais e IPs): resultado do
  `terraform apply`, uma consulta no Athena, o **dashboard completo** no
  Superset (com o filtro em uso) e o `terraform destroy` concluído;
- a apresentação final (arquivo ou link).

## Critérios de avaliação

| Critério | Peso |
|---|---|
| Views gold corretas (nomes de colunas e regras de negócio) | 25% |
| Dashboard interativo: 6+ gráficos, filtro, títulos claros | 30% |
| Insights e recomendação com números (storytelling) | 25% |
| Pitch e arguição técnica | 15% |
| Evidências e encerramento da infra (`destroy`) | 5% |

## O que o CI verifica

- Se todas as seções de texto do `FINAL_REPORT.md` foram preenchidas
  (Resumo dos Resultados, Visualizações Criadas, Lições Aprendidas,
  Referências);
- Se **todos os itens do checklist de entregáveis** foram marcados (`[x]`).

O dashboard, os SQLs e o pitch são avaliados manualmente pelo professor.

## Problemas comuns

- **`ExpiredToken` / 403:** as credenciais do Learner Lab expiram; reexporte
  as de *AWS Details*.
- **Bucket já existe:** o nome é global; troque `bucket_nome`.
- **Athena pede local de resultados:** você não selecionou o workgroup do output.
- **Superset não abre:** espere ~8 min; confira se `meu_ip_cidr` é o seu IP
  atual (mudou de rede? rode `terraform apply` de novo após atualizá-lo). Para
  ver o andamento: console EC2 → instância `aula14-superset` → *Actions →
  Monitor and troubleshoot → Get system log*, ou `/var/log/superset-setup.log`
  (termina em `SUPERSET PRONTO`).
- **Gráfico do Superset com erro de permissão:** a EC2 precisa do perfil
  `LabInstanceProfile` (padrão do Terraform).
- **Sem tempo/recurso para o Superset:** use `criar_superset = false` e o Plano B.

## Como rodar os testes localmente

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Como entregar

Uma PR por GRUPO — esta é a entrega final do projeto. Veja o
[README principal](../README.md#como-entregar-um-lab).
