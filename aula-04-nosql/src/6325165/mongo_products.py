"""Solucao do lab de operacoes basicas com MongoDB."""


def insert_products(collection, products):
    """Insere os produtos e retorna a quantidade inserida."""
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    """Retorna produtos da categoria, ordenados por preco crescente."""
    cursor = collection.find(
        {"category": category},
        {"_id": 0},
    ).sort("price", 1)
    return list(cursor)


def average_price_by_category(collection):
    """Calcula o preco medio por categoria com um pipeline MongoDB."""
    pipeline = [
        {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}
    ]
    return {
        document["_id"]: document["avg_price"]
        for document in collection.aggregate(pipeline)
    }


def increment_stock(collection, product_id, delta):
    """Atualiza o estoque atomicamente e retorna seu novo valor."""
    result = collection.update_one(
        {"product_id": product_id},
        {"$inc": {"stock": delta}},
    )
    if result.matched_count == 0:
        return None

    product = collection.find_one(
        {"product_id": product_id},
        {"_id": 0, "stock": 1},
    )
    return product["stock"]
