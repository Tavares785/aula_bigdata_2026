# Evidências - Aula 14: Visualização e Conclusão

Execução no AWS Academy Learner Lab (região `us-east-1`). Credenciais e senha
do Superset não aparecem nos prints.

| # | Evidência | Arquivo |
|---|---|---|
| 1 | `terraform apply` concluído (8 recursos criados) e outputs | `01-apply.png` |
| 2 | Views criadas e consultadas no Athena | `02-athena.png` |
| 3 | Dashboard MercadoFácil no Superset (tela de edição) | `03-dashboard.png` |
| 4 | `terraform destroy` concluído (estado vazio) | `04-destroy.png` |

## Observações

- O dashboard foi salvo com 6 gráficos. O gráfico "Nota média por faixa de
  atraso" foi criado, mas ficou fora do dashboard salvo, e o filtro nativo por
  categoria não chegou a ser gravado.
- O `03-dashboard.png` mostra a tela de edição, porque o ambiente foi
  desligado em seguida.
- `terraform destroy` concluído: estado vazio, bucket removido e EC2 do
  Superset encerrada.

## Views criadas no Athena

`vw_atraso_nota`, `vw_problemas_categoria`, `vw_serie_diaria`, `vw_kpis`,
`vw_atraso_chuva`, `vw_feriados`, a bônus `vw_desconto_problemas` e as duas
views prontas `vw_vendas_mensal` e `vw_logistica_estado`. Os SQLs estão em
`aws-lab/sql/03_views_atividade.sql`.
