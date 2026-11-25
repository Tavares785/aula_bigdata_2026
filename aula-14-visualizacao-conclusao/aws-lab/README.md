# aws-lab - Aula 14

Infra (Terraform), dados e SQL da atividade. O roteiro completo está no
[README da aula](../README.md).

```
infra/     Terraform pronto: S3 + Glue Catalog + Athena + (opcional) EC2 com Superset
data/      pedidos_mercadofacil_tratado.csv (10.000 linhas), chuva_diaria.csv, feriados.csv e gerar_dados.py (professor)
sql/       01 validar, 02 views prontas, 03 views que o grupo cria
scripts/   buscar_apis.py (Open-Meteo e BrasilAPI), dashboard_local.py (Plano B, sem AWS)
```

Nota para o professor: `data/gerar_dados.py` regera o CSV de forma
determinística (semente fixa). O atraso nele depende da chuva real do destino e de feriados (efeito planejado: atraso médio de ~0,5 dia sem chuva a ~1,9 dia com chuva acima de 40 mm; o Norte soma chuva e região, então vale discutir causa x correlação). O gabarito das views está em
`lab-professor/aula-14-visualizacao-conclusao/gabarito/atividade/`.
