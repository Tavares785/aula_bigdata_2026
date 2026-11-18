# Checkpoint de Progresso - Aula 13: Análise e Construção de Modelos

Emar Cristian Silva Teruo Ito — RA 6325192 — projeto individual MercadoFácil.

## Análise/modelo implementado

Análise descritiva em PySpark sobre a Silver reconstruída localmente pelo ETL da Aula 12 (`5ccc0cbee58006cdea6ceb4f63074bbfd9ac20cb`). Foram calculados indicadores logísticos por pedido, estado, transportadora e centro de distribuição; notas por situação do prazo; e valores comerciais por categoria e mês. Não foi treinado modelo preditivo, pois o objetivo definido é descritivo. Os agregados estão em `resultados/` (CSV e JSON).

## Principais resultados até agora

- Conciliação: 10000 linhas brutas, 4087 itens Silver e 5913 registros em quarentena.
- Dos 3544 pedidos únicos, 3229 têm prazo conhecido e 729 apresentaram atraso (22.5766% dos mensuráveis). Média de atraso: 1.2629 dias, incluindo pontuais.
- Maiores taxas por UF (mínimo de 30 pedidos mensuráveis): AM: 42.1053% (32/76); CE: 36.5854% (60/164); PE: 35.4067% (74/209).
- Transportadoras: correios: 25.9316% (341/1315); jadlog: 21.118% (136/644); loggi: 19.8473% (156/786).
- Centros de distribuição: cd-nordeste: 35.0649% (189/539); cd-norte: 34.3284% (46/134); cd-sul: 20.0393% (102/509).
- Avaliações: atrasado: média 2.6919, 701 pedidos avaliados; pontual: média 4.1363, 2400 pedidos avaliados; prazo desconhecido: média 3.9661, 59 pedidos avaliados. Comparação observacional, sem inferência causal.
- Valor bruto: R$ 1.446.813,51; valor sem cancelamentos/devoluções explícitos: R$ 1.314.388,47. Maior combinação categoria/mês: eletrônicos / 2025-12, R$ 67.924,75. Não equivale à receita líquida contábil.

## Iterações e ajustes feitos

Foi necessário reproduzir a Silver porque o ambiente AWS da Aula 12 foi destruído. O mesmo código ETL e o mesmo CSV foram usados (SHA-256: `e4a9a835adcd3b306212b7e127733490239bfc5a0704b369b1e2d45f5792f01a`). Para evitar dupla contagem, atrasos são agregados primeiro por pedido, com máximo do atraso conhecido; valores monetários permanecem no nível de item. Prazos e notas ausentes não são imputados; foram definidos denominadores explícitos. Pedidos associados a múltiplos valores de uma dimensão podem aparecer em mais de um grupo, portanto contagens por grupo não devem ser somadas como total único. O recorte mínimo de 30 é apenas um critério descritivo para destacar grupos com maior base. A execução conciliou integralmente as duas tabelas Gold reproduzidas com os novos indicadores, além de verificar ausência de identificadores pessoais diretos e balanço das contagens. Spark 3.5.3 em Docker local, sem nova infraestrutura AWS.

## Próxima etapa (Aula 14)

Construir visualizações de atrasos por UF, transportadora e centro, evolução mensal das vendas e comparação de avaliações. Mostrar denominadores, grupos pequenos e prazos desconhecidos; documentar limitações, recomendações operacionais e conclusões sem atribuir causalidade.
