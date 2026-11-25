# Pitch final - MercadoFácil (8 min)

Grupo: Weslley Lucas (RA 6325226), Gabriel Reis Cunha (RA 6325149) e
Sirlande Martins (RA 6325269).

## 1. Problema (1 min)

- A MercadoFácil faturou R$ 3,3 milhões em 2025 (6.706 pedidos entregues).
- 16,3% dos itens entregues atrasam, a nota média é 4,11 e 7,6% dos itens são
  cancelados ou devolvidos.
- Pergunta da diretoria: onde e por que atrasa, quanto isso custa, e como a
  Black Friday e o Natal pressionam a operação.

## 2. Arquitetura (2 min)

```
CSV + APIs públicas (Open-Meteo, BrasilAPI)
   -> S3 -> Glue Catalog (pedidos, chuva_diaria, feriados)
   -> Athena (views gold, workgroup próprio)
   -> Superset na EC2 (dashboard com filtros)
Tudo criado por 1 terraform apply e removido por 1 terraform destroy.
```

- Aulas 12 e 13: ingestão, ETL no Glue e modelo de atraso no Spark MLlib.
- Aula 14: 8 views gold, mais as 2 prontas. As regras de negócio ficam nas
  views: o denominador de cada métrica e a média ponderada por itens.
- Validação: os mesmos SQLs rodaram em DuckDB local e no Athena, com números
  iguais.

## 3. Demonstração ao vivo (4 min)

Roteiro no dashboard (ou no print `evidencias/02_...` se a AWS estiver fora):

1. **Big Numbers:** como está o negócio.
2. **Série diária:** zoom na Black Friday. Em 28/11 foram 160 pedidos, cerca
   de 8 vezes a média. Nov–dez têm +70% de pedidos.
3. **Atraso × nota:** a nota cai de 4,39 (no prazo) para 1,24 (8+ dias). A
   devolução sobe de 3% para 16%.
4. **Região × transportadora:** aplicar o filtro **Região = Norte**. A Jadlog
   tem 2,24 dias de atraso médio e 38,9% de itens atrasados.
5. **Chuva:** o atraso vai de 0,49 para 1,93 dia. No gráfico chuva × região,
   o efeito aparece dentro de cada região. Por isso falamos em correlação
   forte, não em causa provada.
6. **Problemas por categoria:** filtro de categoria. Beleza e Saúde tem o
   maior cancelamento e Brinquedos, a maior devolução.

**Recomendação:**

- Trocar a transportadora no Norte.
- Usar prazo dinâmico com previsão de chuva, validado com teste A/B.
- Reforçar a capacidade em nov–dez.

## 4. Lições aprendidas (1 min)

- Com IaC, o laboratório sobe e some em minutos: 8 recursos criados e
  destruídos.
- A camada gold define a verdade do negócio. Um denominador errado muda a
  conclusão.
- Correlação não é causa: quebrar por região antes de concluir.
- Dashboard como código (API do Superset) torna a entrega reprodutível.
