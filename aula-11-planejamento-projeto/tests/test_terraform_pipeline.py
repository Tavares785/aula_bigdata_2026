"""
Aula 11 - Verifica se o grupo CONSTRUIU a infra Terraform do pipeline.

Checagem estrutural (sem acessar a AWS) sobre os arquivos *.tf que o grupo
criou em aws-lab/infra/. Os nomes de arquivos, variaveis e recursos sao
livres: o teste so exige que existam os tipos de recurso do pipeline e que
as regras do Learner Lab sejam respeitadas. Comentarios sao ignorados.
"""
import glob
import os
import re

INFRA = os.path.join(os.path.dirname(__file__), "..", "aws-lab", "infra")


def _read_hcl():
    files = sorted(glob.glob(os.path.join(INFRA, "*.tf")))
    assert files, (
        "Nenhum arquivo .tf em aws-lab/infra/. Crie a infra Terraform do "
        "pipeline (veja o README da aula)."
    )
    lines = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            lines += [ln for ln in f.read().splitlines() if not ln.lstrip().startswith("#")]
    return "\n".join(lines)


def _blocks(hcl, rtype):
    """Retorna os corpos de todos os blocos `resource "<rtype>" "<nome>"`."""
    bodies = []
    for m in re.finditer(rf'resource\s+"{rtype}"\s+"[^"]+"\s*\{{', hcl):
        depth, i = 1, m.end()
        while depth and i < len(hcl):
            depth += {"{": 1, "}": -1}.get(hcl[i], 0)
            i += 1
        bodies.append(hcl[m.end():i])
    return bodies


def test_provider_aws_us_east_1():
    hcl = _read_hcl()
    assert re.search(r'provider\s+"aws"', hcl), "Declare o provider aws."
    assert "us-east-1" in hcl, "A regiao do Learner Lab e us-east-1."


def test_bucket_not_created_with_aws_s3_bucket_and_no_iam():
    hcl = _read_hcl()
    assert not re.search(r'resource\s+"aws_s3_bucket"\s', hcl), (
        "Nao use aws_s3_bucket no Learner Lab (SCP nega GetBucketObjectLockConfiguration)."
    )
    assert not re.search(r'resource\s+"aws_iam_(role|policy)', hcl), (
        "Nao crie roles/policies IAM no Learner Lab: use a LabRole."
    )
    assert "local-exec" in hcl and "s3api create-bucket" in hcl, (
        "Crie o bucket via AWS CLI (terraform_data + local-exec)."
    )


def test_dataset_is_uploaded_to_s3():
    assert "pedidos_mercadofacil.csv" in _read_hcl(), (
        "O Terraform deve enviar data/pedidos_mercadofacil.csv para o S3."
    )


def test_glue_database_declared():
    assert _blocks(_read_hcl(), "aws_glue_catalog_database"), (
        "Declare um aws_glue_catalog_database."
    )


def test_glue_job_declared():
    jobs = _blocks(_read_hcl(), "aws_glue_job")
    assert jobs, "Declare um aws_glue_job."
    body = jobs[0]
    assert re.search(r"role_arn\s*=", body), "O Glue Job precisa de role_arn (LabRole)."
    assert re.search(r'name\s*=\s*"glueetl"', body), 'command.name deve ser "glueetl".'
    assert "script_location" in body and "s3://" in body


def test_glue_crawler_declared_with_s3_targets():
    crawlers = _blocks(_read_hcl(), "aws_glue_crawler")
    assert crawlers, "Declare um aws_glue_crawler."
    body = crawlers[0]
    assert re.search(r"role\s*=", body), "O Crawler precisa de role (LabRole)."
    assert re.search(r"database_name\s*=", body)
    assert re.search(r"\bs3_target\s*\{", body), "O Crawler precisa de ao menos um s3_target."


def test_outputs_declared():
    hcl = _read_hcl()
    assert len(re.findall(r'output\s+"[^"]+"', hcl)) >= 3, (
        "Declare outputs uteis (ex.: bucket, job, crawler, database)."
    )
