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
    """
    Recebe uma `collection` (pymongo Collection) e uma lista de
    dicionarios `products`, insere todos de uma vez (`insert_many`), e
    retorna a QUANTIDADE de documentos inseridos.
    """
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    """
    Busca todos os documentos da `collection` cujo campo "category"
    seja igual a `category`, ORDENADOS por "price" CRESCENTE. Retorna
    como uma lista de dicionarios, SEM o campo "_id".
    """
    cursor = collection.find(
        {"category": category},
        {"_id": 0}
    ).sort("price", 1)
    return list(cursor)


def average_price_by_category(collection):
    """
    Usa o pipeline de agregacao do MongoDB para calcular o PRECO MEDIO
    ("price") agrupado por "category". Retorna um dicionario
    {category: preco_medio}.
    """
    pipeline = [
        {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}
    ]
    result = collection.aggregate(pipeline)
    return {doc["_id"]: doc["avg_price"] for doc in result}


def increment_stock(collection, product_id, delta):
    """
    Incrementa (ou decrementa, se `delta` for negativo) o campo "stock"
    do produto cujo "product_id" seja igual a `product_id`, usando o
    operador atomico `$inc`. Depois, busca o documento atualizado e
    retorna o NOVO valor de "stock".

    Se nenhum produto com esse `product_id` existir, retorna `None`.
    """
    update_result = collection.update_one(
        {"product_id": product_id},
        {"$inc": {"stock": delta}}
    )
    if update_result.matched_count == 0:
        return None
    doc = collection.find_one({"product_id": product_id}, {"_id": 0})
    return doc["stock"]
