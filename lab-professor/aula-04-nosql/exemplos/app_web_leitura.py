"""
Aula 04 - NoSQL com MongoDB
Exemplo didatico: simulando a CAMADA DE LEITURA de um aplicativo web.

Ideia
-----
Em um cenario de Big Data, o dado fica em um banco (aqui, MongoDB) e a
aplicacao web NAO carrega tudo de uma vez: ela conecta, consulta apenas
o que precisa e devolve para a tela. Este script mostra esse fluxo de
forma bem simples, do jeito que um backend web faria:

    conectar  ->  consultar  ->  formatar  ->  exibir

Pre-requisitos:
    docker compose up -d          # sobe o MongoDB real (localhost:27017)
    docker compose exec -T aula04-mongodb mongoimport --db loja \\
        --collection produtos --drop --file /data/sample/produtos.jsonl
    pip install pymongo

    python exemplos/app_web_leitura.py
"""

from pymongo import MongoClient

# Onde o MongoDB esta rodando (o mesmo do docker-compose.yml da aula).
MONGO_URI = "mongodb://localhost:27017"
DB = "loja"
COLECAO = "produtos"


def conectar():
    """Abre a conexao com o MongoDB e devolve a colecao de produtos."""
    client = MongoClient(MONGO_URI)
    return client[DB][COLECAO]


def listar_produtos(colecao, categoria=None):
    """
    Le os produtos do banco (como um endpoint '/produtos' faria).

    Se 'categoria' for informada, filtra por ela. Usamos projecao para
    NAO trazer o campo interno '_id' e ordenamos por preco.
    """
    filtro = {"category": categoria} if categoria else {}
    return list(
        colecao.find(filtro, {"_id": 0}).sort("price", 1)
    )


def exibir(produtos):
    """Formata cada produto em uma linha legivel, como apareceria na tela."""
    if not produtos:
        print("  (nenhum produto encontrado)")
        return
    for p in produtos:
        print(
            f"  [{p['product_id']:>3}] {p['nome']:<28} | "
            f"{p['category']:<12} | R$ {p['price']:>8.2f} | "
            f"estoque: {p['stock']:>3}"
        )


def main():
    colecao = conectar()

    print("\n=== Catalogo completo (o app pediu tudo) ===")
    exibir(listar_produtos(colecao))

    print("\n=== Apenas 'eletronicos' (o usuario filtrou na tela) ===")
    exibir(listar_produtos(colecao, categoria="eletronicos"))

    total = colecao.count_documents({})
    print(f"\nTotal de produtos no banco: {total}")


if __name__ == "__main__":
    main()
