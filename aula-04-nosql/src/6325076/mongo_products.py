"""
Aula 04 - Modelos e Implementacoes NoSQL
Lab: Operacoes basicas em um banco de dados orientado a documentos
(MongoDB), usando a API real do pymongo.
"""


def insert_products(collection, products):
    """
    Insere todos os produtos de uma vez e retorna a quantidade inserida.
    """
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    """
    Busca produtos por categoria, ordenados por preco crescente,
    sem retornar o campo _id.
    """
    return list(
        collection.find(
            {"category": category},
            {"_id": 0}
        ).sort("price", 1)
    )


def average_price_by_category(collection):
    """
    Calcula o preco medio dos produtos agrupados por categoria.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "avg_price": {"$avg": "$price"}
            }
        }
    ]

    result = collection.aggregate(pipeline)

    return {
        item["_id"]: item["avg_price"]
        for item in result
    }


def increment_stock(collection, product_id, delta):
    """
    Incrementa ou decrementa o estoque de um produto usando $inc.
    Retorna o novo estoque ou None se o produto nao existir.
    """
    result = collection.update_one(
        {"product_id": product_id},
        {"$inc": {"stock": delta}}
    )

    if result.matched_count == 0:
        return None

    product = collection.find_one(
        {"product_id": product_id},
        {"_id": 0, "stock": 1}
    )

    return product["stock"]
