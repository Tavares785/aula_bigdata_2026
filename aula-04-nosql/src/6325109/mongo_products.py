"""
Aula 04 - Modelos e Implementacoes NoSQL
Lab: Operacoes basicas em um banco de dados orientado a documentos
(MongoDB), usando a API real do pymongo.

Entrega de: Carina Dalpino - RA 6325109

Contexto
--------
Os testes injetam uma "collection" que implementa a MESMA interface do
pymongo (via `mongomock`, uma biblioteca que simula o MongoDB em
memoria). Ou seja: o codigo que voce escreve aqui e EXATAMENTE o mesmo
que voce escreveria contra um MongoDB de verdade -- so que os testes
automaticos nao dependem de nenhum servidor rodando.
"""


def insert_products(collection, products):
    """
    Insere todos os documentos de uma vez (insert_many) e retorna a
    quantidade de documentos inseridos.
    """
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    """
    Busca documentos por "category", ordenados por "price" crescente,
    excluindo o campo "_id" da projecao.
    """
    cursor = collection.find({"category": category}, {"_id": 0}).sort("price", 1)
    return list(cursor)


def average_price_by_category(collection):
    """
    Calcula o preco medio agrupado por "category" via pipeline de
    agregacao e retorna {category: preco_medio}.
    """
    pipeline = [
        {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}
    ]
    return {doc["_id"]: doc["avg_price"] for doc in collection.aggregate(pipeline)}


def increment_stock(collection, product_id, delta):
    """
    Incrementa/decrementa "stock" via operador atomico $inc e retorna o
    novo valor. Retorna None se o produto nao existir.
    """
    result = collection.update_one(
        {"product_id": product_id},
        {"$inc": {"stock": delta}}
    )

    if result.matched_count == 0:
        return None

    updated = collection.find_one({"product_id": product_id})
    return updated["stock"]
