# AWS Lab - Pipeline de Dados MercadoFácil

Pipeline de ingestão e pré-processamento de dados na AWS usando Terraform, S3, Glue e Athena.

## Arquitetura

```
┌─────────┐     ┌───────────┐     ┌─────────────┐     ┌─────────┐
│ CSV Raw │ --> │ Glue Job  │ --> │ S3 (Parquet)│ --> │ Athena  │
│  (raw)  │     │ (PySpark) │     │ silver/gold │     │ (SQL)   │
└─────────┘     └───────────┘     └─────────────┘     └─────────┘
                      │
                      └─────────> Glue Crawler
```

**Camadas de dados:**
- **raw**: CSV original sem modificações
- **silver**: Dados limpos, tipados, deduplicados e anonimizados (Parquet)
- **gold**: Tabelas analíticas agregadas para responder perguntas de negócio (Parquet)
- **quarantine**: Registros com problemas de qualidade (Parquet)

## Estrutura do Projeto

```
aws-lab/
├── infra/                  # Infraestrutura como código (Terraform)
│   ├── provider.tf         # Configuração do provider AWS
│   ├── variables.tf        # Variáveis de entrada
│   ├── s3.tf              # Bucket S3 (via AWS CLI) e uploads
│   ├── glue.tf            # Glue Database, Job e Crawlers
│   ├── outputs.tf         # Outputs úteis (nomes de recursos)
│   └── terraform.tfvars.example  # Exemplo de variáveis (copiar e editar)
├── job/                   # Script ETL PySpark
│   └── etl_mercadofacil.py  # Pipeline raw -> silver -> gold
├── scripts/               # Scripts auxiliares
│   ├── setup.sh          # Setup inicial (obter LabRole ARN)
│   └── run_pipeline.sh   # Executar job + crawlers
├── REGRAS_SILVER.md      # Documentação dos problemas de qualidade e regras
└── README.md             # Este arquivo
```

## Pré-requisitos

1. **AWS Academy Learner Lab** ativo
2. **Credenciais AWS** configuradas (via variáveis de ambiente)
3. **Terraform** instalado (versão >= 1.0)
4. **AWS CLI** instalado e configurado

## Guia de Uso

### 1. Configurar Credenciais AWS

No AWS Academy Learner Lab, clique em **AWS Details → Show** e copie os comandos de exportação:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
```

⚠️ **Importante:** As credenciais expiram após algumas horas. Você precisará renová-las.

### 2. Setup Inicial

Execute o script de setup para obter o ARN da LabRole e gerar o `terraform.tfvars`:

```bash
cd aws-lab/scripts
bash setup.sh
```

O script irá:
- Validar suas credenciais AWS
- Obter o ARN da LabRole automaticamente
- Solicitar um nome único para o bucket S3
- Gerar o arquivo `terraform.tfvars`
- Inicializar o Terraform

### 3. Provisionar Infraestrutura

```bash
cd ../infra
terraform plan    # Revisar as mudanças
terraform apply   # Criar recursos na AWS
```

Recursos criados:
- Bucket S3 (via AWS CLI)
- Upload do CSV para `s3://BUCKET/raw/`
- Upload do script PySpark para `s3://BUCKET/scripts/`
- Glue Database `mercadofacil_db`
- Glue Job `mercadofacil-bigdata-etl-job`
- Glue Crawlers para silver e gold

### 4. Executar o Pipeline

```bash
cd ../scripts
bash run_pipeline.sh
```

O script irá:
1. Iniciar o Glue Job (ETL)
2. Aguardar a conclusão do job
3. Executar o Crawler Silver (catalogar dados limpos)
4. Executar o Crawler Gold (catalogar tabelas analíticas)

⏱️ **Tempo estimado:** 5-10 minutos

### 5. Consultar Dados no Athena

Acesse o console do Athena: https://console.aws.amazon.com/athena/

Selecione o database `mercadofacil_db` e explore as tabelas da camada gold:

#### Exemplo 1: Regiões com Maior Taxa de Atraso

```sql
SELECT 
    estado,
    centro_distribuicao,
    total_pedidos,
    ROUND(taxa_atraso_pct, 2) AS taxa_atraso,
    ROUND(atraso_medio_dias, 1) AS atraso_medio
FROM analise_atrasos_avaliacoes
WHERE total_pedidos > 10
ORDER BY taxa_atraso_pct DESC
LIMIT 10;
```

#### Exemplo 2: Categorias com Maior Taxa de Cancelamento

```sql
SELECT 
    categoria,
    estado,
    SUM(total_pedidos) AS pedidos,
    SUM(total_cancelados) AS cancelamentos,
    ROUND(AVG(taxa_cancelamento_pct), 2) AS taxa_cancel_media
FROM analise_cancelamentos_devolucoes
GROUP BY categoria, estado
ORDER BY taxa_cancel_media DESC
LIMIT 10;
```

#### Exemplo 3: Sazonalidade (Black Friday e Natal)

```sql
SELECT 
    ano,
    mes,
    mes_nome,
    SUM(total_pedidos) AS total_pedidos,
    ROUND(SUM(receita_total), 2) AS receita_total,
    ROUND(AVG(atraso_medio_dias), 1) AS atraso_medio,
    SUM(cancelamentos + devolucoes) AS problemas
FROM analise_sazonalidade
WHERE mes IN (11, 12)  -- Novembro (Black Friday) e Dezembro (Natal)
GROUP BY ano, mes, mes_nome
ORDER BY ano, mes;
```

### 6. Limpar Recursos (Destroy)

⚠️ **Antes de destruir**, salve suas queries e resultados do Athena!

```bash
cd ../infra
terraform destroy
```

Isso irá:
- Esvaziar e deletar o bucket S3
- Remover o Glue Job, Crawlers e Database
- Liberar todos os recursos AWS

## Tabelas Gold Disponíveis

### 1. `analise_atrasos_avaliacoes`

Análise de atrasos de entrega e sua relação com avaliações.

**Colunas:**
- `estado`, `categoria`, `transportadora`, `centro_distribuicao`
- `total_pedidos`, `pedidos_atrasados`, `taxa_atraso_pct`
- `atraso_medio_dias`, `atraso_maximo_dias`
- `nota_media`, `avaliacoes_baixas`, `taxa_avaliacao_baixa_pct`
- `prazo_estimado_medio`, `prazo_real_medio`

**Perguntas que responde:**
- Quais fatores mais explicam o atraso? (estado, categoria, transportadora)
- Qual a relação entre atraso e nota de avaliação?
- Quais centros de distribuição têm pior desempenho?

### 2. `analise_cancelamentos_devolucoes`

Análise de cancelamentos e devoluções por dimensões de negócio.

**Colunas:**
- `estado`, `categoria`, `canal`, `forma_pagamento`
- `total_pedidos`, `total_cancelados`, `total_devolvidos`
- `taxa_cancelamento_pct`, `taxa_devolucao_pct`, `taxa_perda_pct`
- `valor_total_vendas`, `ticket_medio`, `clientes_unicos`

**Perguntas que responde:**
- Quais categorias, canais e estados têm mais cancelamento/devolução?
- Existe relação entre forma de pagamento e cancelamento?
- Qual o impacto financeiro de cancelamentos e devoluções?

### 3. `analise_sazonalidade`

Análise mês a mês de vendas, entregas e problemas.

**Colunas:**
- `ano`, `mes`, `mes_nome`, `categoria`
- `total_pedidos`, `receita_total`
- `atraso_medio_dias`, `cancelamentos`, `devolucoes`, `nota_media`

**Perguntas que responde:**
- Como a sazonalidade (Black Friday, Natal) afeta vendas?
- Como a sazonalidade afeta a logística (atrasos)?
- Quais categorias vendem mais em cada época do ano?

### 4. `fato_pedidos`

Tabela de fatos com todos os pedidos (dimensão mais granular).

**Colunas:** Todas as colunas de negócio (dados anonimizados).

**Uso:** Base para análises customizadas não cobertas pelas tabelas gold agregadas.

## Detalhes Técnicos

### Qualidade de Dados

Consulte [REGRAS_SILVER.md](./REGRAS_SILVER.md) para a lista completa de problemas de qualidade encontrados e as regras de transformação aplicadas.

Principais problemas tratados:
1. Formatos de data inconsistentes
2. Valores monetários em múltiplos formatos
3. Padronização de texto (case, espaços)
4. Valores nulos representados de múltiplas formas
5. CPF e email em formato inválido
6. Duplicatas de registros
7. Anonimização de dados pessoais (LGPD)

### LGPD e Privacidade

Os campos `cliente_nome`, `cliente_email`, `cliente_cpf` e `comentario` são:
- Substituídos por hashes SHA-256 na camada silver
- Removidos completamente (os originais não são mantidos)
- Isso permite análises agregadas por cliente sem expor dados pessoais

### Quarentena

Registros com problemas críticos são isolados em `s3://BUCKET/quarantine/pedidos_invalidos/` com um campo `motivo_quarentena` explicando o problema. Isso permite revisão manual e eventual correção na fonte.

## Troubleshooting

### Erro: "Bucket name already exists"

Nomes de bucket S3 são globais. Escolha um nome único incluindo seu grupo ou ID.

### Erro: "Access Denied" ao criar bucket

Verifique se suas credenciais AWS estão válidas. No Learner Lab, as credenciais expiram após algumas horas.

### Job Glue falha

1. Verifique os logs no CloudWatch:
   - `/aws-glue/jobs/output` (stdout)
   - `/aws-glue/jobs/error` (stderr)
2. Verifique se o script PySpark foi enviado corretamente para o S3
3. Verifique se o ARN da LabRole está correto

### Crawler não encontra dados

1. Verifique se o Glue Job foi concluído com sucesso (status SUCCEEDED)
2. Verifique se os dados foram escritos no S3 (console S3 ou AWS CLI)
3. Aguarde alguns segundos após o job terminar antes de rodar o crawler

### Terraform fmt/validate falha

Execute:
```bash
terraform fmt      # Formata todos os arquivos .tf
terraform validate # Valida a sintaxe
```

## Contribuindo

Este projeto faz parte da **Aula 12: Ingestão e Pré-processamento** do curso de Big Data.

Grupo: [PREENCHER]

Integrantes:
- [PREENCHER]
- [PREENCHER]
- [PREENCHER]

## Referências

- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/)
- [Terraform AWS Provider 5.31.0](https://registry.terraform.io/providers/hashicorp/aws/5.31.0/docs)
- [PySpark SQL Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Amazon Athena User Guide](https://docs.aws.amazon.com/athena/)
