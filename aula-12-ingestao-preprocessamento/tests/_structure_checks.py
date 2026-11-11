"""
Utilitarios de verificacao estrutural, usados pelos testes das Aulas
12, 13 e 14 (etapas de projeto livre, sem uma unica resposta certa).

Estas funcoes checam SE o aluno implementou algo (estrutura), nao SE a
implementacao esta "correta" -- isso e avaliado pelo professor, ja que
cada grupo trabalha com um dataset e problema diferente.
"""
import ast
import os
import re


def read_text(path):
    assert os.path.exists(path), f"Arquivo nao encontrado: {path}"
    with open(path, encoding="utf-8") as f:
        return f.read()


def assert_function_implemented(file_path, func_name, min_statements=1):
    """Verifica que a funcao `func_name` existe em `file_path`, nao
    contem mais nenhum `raise NotImplementedError`, e tem pelo menos
    `min_statements` instrucoes reais no corpo (ignorando a docstring),
    ou seja, nao foi deixada como `pass`/`...`/vazia."""
    source = read_text(file_path)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            func_source = ast.get_source_segment(source, node) or ""
            assert "NotImplementedError" not in func_source, (
                f"A funcao '{func_name}' em {os.path.basename(file_path)} "
                "ainda contem 'raise NotImplementedError' -- implemente-a."
            )

            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(
                getattr(body[0], "value", None), ast.Constant
            ) and isinstance(body[0].value.value, str):
                body = body[1:]  # ignora a docstring

            assert len(body) >= min_statements, (
                f"A funcao '{func_name}' em {os.path.basename(file_path)} "
                "parece vazia (sem implementacao real)."
            )
            for stmt in body:
                if isinstance(stmt, ast.Pass):
                    raise AssertionError(
                        f"A funcao '{func_name}' contem apenas 'pass' -- implemente-a."
                    )
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is Ellipsis
                ):
                    raise AssertionError(
                        f"A funcao '{func_name}' contem apenas '...' -- implemente-a."
                    )
            return

    raise AssertionError(f"Funcao '{func_name}' nao encontrada em {file_path}")


def assert_section_filled(content, header, min_chars=20):
    pattern = re.compile(
        rf"^{re.escape(header)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    assert match, f"Secao '{header}' nao encontrada no documento"
    body = match.group(1).strip()
    assert "<PREENCHER" not in body.upper(), (
        f"Secao '{header}' ainda contem o placeholder '<PREENCHER...>' do template."
    )
    assert len(body) >= min_chars, (
        f"Secao '{header}' parece vazia ou curta demais "
        f"(minimo de {min_chars} caracteres)."
    )
