# Etapa do Projeto - Aula 11: Definição e Planejamento

## Objetivo

Escolher o problema, definir os objetivos, o(s) dataset(s) e as
ferramentas de Big Data que o seu grupo vai usar no projeto final
(concluído na Aula 14).

## Importante: esta etapa não tem "resposta certa"

Diferente dos labs das Aulas 2 a 10, aqui **não existe uma implementação
de referência** — cada grupo escolhe seu próprio problema e dataset. A
correção automática (CI) verifica apenas se você **preencheu de fato**
todas as seções obrigatórias da proposta, e não se o conteúdo está
"certo" (isso é avaliado pelo professor, na revisão da PR).

## O que você precisa fazer

Edite o arquivo `PROJECT_PROPOSAL.md` (nesta mesma pasta), substituindo
cada `<PREENCHER: ...>` pelo conteúdo real do seu grupo, nas seções:

- Integrantes do Grupo
- Problema
- Objetivos
- Dataset(s) e Fonte
- Ferramentas de Big Data
- Cronograma

**Não apague os títulos das seções** (as linhas com `##`) — o CI usa
eles para localizar cada parte do documento.

## Como rodar os testes localmente

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Como entregar

Cada GRUPO faz UMA PR (não uma por pessoa). Veja o
[README principal](../README.md#como-entregar-um-lab) para o fluxo de
fork → branch → PR, e coloque o nome de todos os integrantes no título
ou na descrição da PR.
