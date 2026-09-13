"""
Aula 04 - Modelos e Implementacoes NoSQL
Lab: Operacoes basicas em um banco de dados orientado a documentos
(MongoDB), usando a API real do pymongo.

Contexto
--------
Os testes injetam uma "collection" que implementa a MESMA interface do
pymongo (via `mongomock`, uma biblioteca que simula o MongoDB em
memoria). Ou seja: o codigo que voce escreve aqui e EXATAMENTE o mesmo
que voce escreveria contra um MongoDB de verdade -- so que os testes
automaticos nao dependem de nenhum servidor rodando.

Como testar localmente antes de enviar a PR:
    pip install -r requirements.txt
    pytest -v
"""


def insert_products(collection, products):
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    cursor = collection.find({"category": category}, {"_id": 0})
    return list(cursor.sort("price", 1))


def average_price_by_category(collection):
    pipeline = [
        {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}
    ]
    result = {}
    for doc in collection.aggregate(pipeline):
        result[doc["_id"]] = doc["avg_price"]
    return result


def increment_stock(collection, product_id, delta):
    result = collection.update_one(
        {"product_id": product_id},
        {"$inc": {"stock": delta}}
    )
    if result.matched_count == 0:
        return None
    doc = collection.find_one({"product_id": product_id})
    return doc["stock"]
