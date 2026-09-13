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
    TODO 1:
    Receba uma `collection` (pymongo Collection) e uma lista de
    dicionarios `products`, insira todos de uma vez (`insert_many`), e
    retorne a QUANTIDADE de documentos inseridos.
    """
    raise NotImplementedError("TODO 1: implemente insert_products")


def find_by_category(collection, category):
    """
    TODO 2:
    Busque todos os documentos da `collection` cujo campo "category"
    seja igual a `category`, ORDENADOS por "price" CRESCENTE. Retorne
    como uma lista de dicionarios, SEM o campo "_id" (use projecao para
    excluir: `{"_id": 0}`).
    """
    raise NotImplementedError("TODO 2: implemente find_by_category")


def average_price_by_category(collection):
    """
    TODO 3:
    Use o pipeline de agregacao do MongoDB (`collection.aggregate([...])`)
    para calcular o PRECO MEDIO ("price") agrupado por "category".
    Retorne um dicionario {category: preco_medio}.

    Dica: um pipeline com um unico estagio `$group` resolve:
        [{"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}]
    """
    raise NotImplementedError("TODO 3: implemente average_price_by_category")


def increment_stock(collection, product_id, delta):
    """
    TODO 4:
    Incremente (ou decremente, se `delta` for negativo) o campo "stock"
    do produto cujo "product_id" seja igual a `product_id`, usando o
    operador atomico `$inc` do MongoDB (`update_one`). Depois, busque o
    documento atualizado e retorne o NOVO valor de "stock".

    Se nenhum produto com esse `product_id` existir, retorne `None`.
    """
    raise NotImplementedError("TODO 4: implemente increment_stock")
