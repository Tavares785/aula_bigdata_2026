"""
Aula 04 - Modelos e Implementacoes NoSQL
Lab: Operacoes basicas em um banco de dados orientado a documentos
(MongoDB), usando a API real do pymongo.
"""


def insert_products(collection, products):
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    cursor = collection.find({"category": category}, {"_id": 0}).sort("price", 1)
    return list(cursor)


def average_price_by_category(collection):
    pipeline = [
        {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}
    ]
    result = collection.aggregate(pipeline)
    return {doc["_id"]: doc["avg_price"] for doc in result}


def increment_stock(collection, product_id, delta):
    result = collection.update_one({"product_id": product_id}, {"$inc": {"stock": delta}})
    if result.matched_count == 0:
        return None
    updated = collection.find_one({"product_id": product_id})
    return updated["stock"]