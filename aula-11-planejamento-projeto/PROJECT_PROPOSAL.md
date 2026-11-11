# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

Carina - 6325109
Luiza - 6325257

## Problema

Academias enfrentam dificuldades em gerenciar a ocupação, identificar
padrões de uso e prever o cancelamento de matrículas (churn). A falta
de análise dos dados de frequência e comportamento dos membros impede
decisões mais eficientes sobre horários, infraestrutura e retenção de
clientes.

## Objetivos

- Identificar os horários e dias de maior fluxo de membros na academia
- Segmentar perfis de alunos por tipo de treino, frequência e nível de
  experiência
- Construir um modelo preditivo para identificar membros com risco de
  cancelamento (churn)

## Dataset(s) e Fonte

- **Dataset:** Gym Members Exercise Dataset
- **Fonte:** Kaggle — [valakhorasani/gym-members-exercise-dataset](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset)
- **Volume:** 973 registros, 15 colunas (idade, gênero, peso, tipo de
  treino, frequência semanal, duração da sessão, calorias queimadas,
  entre outros)
- **Formato:** CSV estático

## Ferramentas de Big Data

- **Apache Spark** — limpeza, transformação e agregação dos dados de
  frequência e comportamento
- **Spark MLlib** — treinamento do modelo de classificação para
  previsão de churn
- **MongoDB** — armazenamento dos perfis processados dos membros
- **Apache Superset** — criação do dashboard interativo com fluxo por
  dia, horário e perfil de aluno

## Cronograma

| Etapa | Descrição |
|-------|-----------|
| 1 | Coleta e exploração do dataset |
| 2 | Limpeza e transformação com Spark |
| 3 | Análise exploratória e segmentação de perfis |
| 4 | Treinamento do modelo de churn com MLlib |
| 5 | Armazenamento no MongoDB |
| 6 | Criação do dashboard no Superset |
| 7 | Apresentação final |
