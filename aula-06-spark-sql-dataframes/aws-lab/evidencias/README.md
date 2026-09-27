# Evidências do lab (entrega por RA)

Esta pasta guarda as **evidências** que comprovam que você executou o lab da
aula-06 na AWS (AWS Glue). As evidências fazem parte da entrega e vão
**versionadas na Pull Request**.

## Como entregar

Cada aluno cria uma subpasta com o **seu RA**:

```
evidencias/<RA>/        # ex.: evidencias/2500123/
```

Dentro dessa subpasta você coloca:

- O arquivo **`EVIDENCIAS.md`**, copiado do template [`TEMPLATE.md`](TEMPLATE.md)
  e devidamente preenchido.
- As **imagens dos prints** referenciadas no seu `EVIDENCIAS.md`
  (ex.: `01-apply.png`, `02-job-success.png`, ...).

Exemplo de estrutura final:

```
evidencias/
└── 2500123/
    ├── EVIDENCIAS.md
    ├── 01-apply.png
    ├── 02-job-success.png
    └── 03-resultado.png
```

## Formatos aceitos

- **Prints**: imagens `.png` ou `.jpg`.
- **Saídas de texto**: cole os trechos diretamente em blocos de código dentro do
  próprio `EVIDENCIAS.md`.

## Regras importantes

- As evidências são **parte da entrega** e devem ir **versionadas na PR**.
- **NUNCA** inclua credenciais ou segredos nos prints. Se aparecerem, **mascare**
  a Access Key, o Secret e o Session Token antes de salvar a imagem.
