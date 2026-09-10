# 🏥 Lab de Banco de Dados: O Caso da Clínica Médica "HealthTech"

Bem-vindo ao laboratório prático de normalização! Neste desafio, você atuará como um DBA responsável por modernizar o sistema legado de uma clínica médica.

## 🎯 Objetivo
O objetivo deste laboratório é aplicar as técnicas de **Normalização de Dados** em um esquema "sujo" extraído de um sistema legado, garantindo que a nova estrutura atenda aos requisitos de **1NF, 2NF e 3NF**.

---

## 📝 O Cenário
Atualmente, todos os dados da clínica estão consolidados em uma única tabela gigante chamada `Relatorio_Geral_Consultas`. 

### Estrutura Atual (Tabela Não Normalizada):
|------------------------|------------------------------------|
| Campo                  | Descrição                          |
|------------------------|------------------------------------|
| `ID_Consulta`          | Identificador único da consulta    |
| `Data` / `Hora`        | Momento do atendimento             |
| `CPF_Paciente`         | Documento do paciente              |
| `Nome_Paciente`        | Nome completo do paciente          |
| `Telefone_Paciente`    | Contato do paciente                |
| `CRM_Medico`           | Registro profissional do médico    |
| `Nome_Medico`          | Nome completo do médico            |
| `Especialidade_Medico` | Área de atuação do médico          |
| `Valor_Consulta`       | Preço cobrado pelo atendimento     |
| `ID_Convenio`          | Identificador do convênio          |
| `Nome_Convenio`        | Nome da operadora de saúde         |
|------------------------|------------------------------------|

---

## 🛠️ Tarefas (Trabalho Final)

### 1. Identificação de Problemas
- **Anomalias:** Liste 2 exemplos de anomalias (inserção, exclusão ou alteração) que podem ocorrer nesta tabela única.
- **Dependências Funcionais:** Identifique as dependências. *Exemplo: O `ID_Convenio` determina o `Nome_Convenio`?*

### 2. Normalização Passo a Passo
Demonstre a evolução do banco de dados em cada etapa:
- **Passo 1:** Demonstre como a tabela ficaria na **1NF**.
- **Passo 2:** Aplique a **2NF** (removendo dependências parciais).
- **Passo 3:** Aplique a **3NF** (removendo dependências transitivas).

### 3. Modelagem Final
- **MER:** Crie o MER.
- **Modelo Lógico:** Desenhe o Modelo Lógico.
- **Script SQL:** Escreva o script DDL (`CREATE TABLE`) para a estrutura normalizada, definindo corretamente as Chaves Primárias (**PK**) e Estrangeiras (**FK**).

---

## 📤 Entrega
Para concluir este lab, siga os passos abaixo:
1. Crie um repositório no seu **GitHub**.
2. Suba o arquivo `projeto_normalizado.sql` com os comandos de criação.
3. Inclua uma imagem ou PDF do seu **Diagrama (DER) e Modelo Logico** na pasta raiz.
4. Edite o arquivo `README.md` do seu repositório com as respostas das questões teóricas (Tarefa 1).

---

## 💡 Dica de Ouro
Ao lidar com a **2NF**, lembre-se: se você tem uma chave primária composta, todos os outros campos devem depender da **chave inteira**. Se um campo depende apenas de "metade" da chave, ele está no lugar errado!

---

## ✅ Respostas (Tarefa 1)

### 1. Identificação de Problemas

**Anomalias na tabela `Relatorio_Geral_Consultas`:**

- **Anomalia de Inserção:** não é possível cadastrar um novo médico ou paciente antes que ele tenha uma consulta marcada, pois `CRM_Medico`/`CPF_Paciente` só existem atrelados a uma linha de consulta.
- **Anomalia de Exclusão:** se a única consulta de um paciente for cancelada e a linha for apagada, todos os dados cadastrais do paciente (nome, telefone) são perdidos junto, mesmo que ele continue sendo cliente da clínica.
- **Anomalia de Atualização:** se um médico mudar de especialidade ou telefone, é preciso atualizar essa informação em *todas* as linhas em que ele aparece; se uma linha for esquecida, a base fica inconsistente (o mesmo médico com dois valores diferentes).

**Dependências Funcionais:**

- `ID_Consulta → Data, Hora, CPF_Paciente, CRM_Medico, Valor_Consulta, ID_Convenio` (a consulta determina todos os dados do atendimento)
- `CPF_Paciente → Nome_Paciente, Telefone_Paciente`
- `CRM_Medico → Nome_Medico, Especialidade_Medico`
- `ID_Convenio → Nome_Convenio` (sim, `ID_Convenio` determina `Nome_Convenio`)

### 2. Normalização Passo a Passo

**Passo 1 — 1NF:** a tabela original já possui apenas valores atômicos (sem listas/repetições em uma célula), então ela satisfaz a 1NF tal como está — o problema é que ela mistura, numa única linha, dados de quatro entidades diferentes (paciente, médico, convênio e consulta).

**Passo 2 — 2NF (remover dependências parciais):** como a tabela não tem chave composta (a chave é `ID_Consulta`), não há dependência parcial a rigor, mas os atributos que não dependem de `ID_Consulta` diretamente (dados de paciente, médico e convênio) são retirados para tabelas próprias, ficando cada um identificado por sua própria chave (`CPF_Paciente`, `CRM_Medico`, `ID_Convenio`):

- `Paciente(CPF_Paciente, Nome_Paciente, Telefone_Paciente)`
- `Medico(CRM_Medico, Nome_Medico, Especialidade_Medico)`
- `Convenio(ID_Convenio, Nome_Convenio)`
- `Consulta(ID_Consulta, Data, Hora, Valor_Consulta, CPF_Paciente, CRM_Medico, ID_Convenio)` — os três últimos como chaves estrangeiras.

**Passo 3 — 3NF (remover dependências transitivas):** em `Consulta`, `Nome_Paciente`/`Telefone_Paciente` dependiam transitivamente de `ID_Consulta` via `CPF_Paciente` (o mesmo vale para os dados de médico e convênio). Ao movê-los para suas próprias tabelas no passo anterior, essa dependência transitiva já foi eliminada — `Consulta` passa a conter apenas atributos que dependem exclusivamente de `ID_Consulta` mais as chaves estrangeiras. O resultado final está em 3FN.

### 3. Modelagem Final

- **MER / DER:** ver [`der_diagrama.svg`](./der_diagrama.svg) — 4 entidades (`Paciente`, `Medico`, `Convenio`, `Consulta`), com `Consulta` em relacionamento N:1 com as demais.
- **Modelo Lógico / Script SQL (DDL):** ver [`projeto_normalizado.sql`](./projeto_normalizado.sql), com PKs em cada entidade e FKs em `Consulta` referenciando `Paciente`, `Medico` e `Convenio`.

---
*Este laboratório faz parte da disciplina de Modelagem de Bancos de Dados Relacionais.*