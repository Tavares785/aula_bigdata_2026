# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

Felipe Mariano | RA:3225014
Maximus Ponciano | RA:6325066
Matheus Mantovani | RA:1120245


## Problema

Seguindo nossa linha de trabalho no controle de documentações e checklists do parque aquático do qual estamos trabalhando em conjunto no projeto final.

Qual é o problema? Atualmente, as rotinas de checklist do parque aquático são realizadas manualmente em folhas de papel. Essa prática dificulta o preenchimento, manuseio e armazenamento adequado dos documentos, os quais frequentemente se deterioram devido ao ambiente úmido. Por se tratar de um processo crítico que envolve diretamente a segurança física de colaboradores e hóspedes, a falta de controle digital impede o acompanhamento ágil de problemas detectados nas atrações.



## Objetivos

Nosso propósito é modernizar e padronizar o processo de vistoria pré-abertura das atrações, substituindo o controle manual em folhas de papel por uma aplicação segura, prática e auditável. O público-alvo são os guarda-vidas (que executam as vistorias em campo), supervisores de operação/manutenção e auditores de segurança.

## Dataset(s) e Fonte

Dados preenchidos manualmente e diariamente pelos usuários da aplicação.

Dados estruturados e padronizados em sua maior parte sendo: valores numéricos para indicar "conforme" e "não conforme" e textos como "observação".


## Ferramentas de Big Data

<PREENCHER: quais ferramentas vistas no curso vocês pretendem usar
(Hadoop, Kafka, Spark, MongoDB/Cassandra/HBase, Hive, Zeppelin/Superset,
MLlib, NLP, etc.) e por que cada uma faz sentido para o problema
escolhido?>

* PortgreSQL -> para persistência íntegra dos documentos, cache/sessão via Redis, mensageria para alerta de não conformidades, infraestrutura provisionada em nuvem AWS via Terraform e esteira de CI/CD automatizada com GitHub Actions.



## Cronograma

Entregar algo funcional até o final deste semestre.

1. Plataforma operando de forma básica.
2. Fluxo de dados estável.
3. Dados tratados e confiáveis.
