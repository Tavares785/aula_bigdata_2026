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
from pymongo import ASCENDING



def insert_products(collection, products):
    """
    TODO 1:
    Receba uma `collection` (pymongo Collection) e uma lista de
    dicionarios `products`, insira todos de uma vez (`insert_many`), e
    retorne a QUANTIDADE de documentos inseridos.
    """
    # insert_many faz UMA viagem ate o banco com o lote inteiro. Um laco
    # com insert_one por documento faria N viagens de rede -- a diferenca
    # aparece rapido quando o lote tem milhares de itens.
    resultado = collection.insert_many(products)

    # O driver devolve os _id gerados; contar eles e mais fiel do que
    # devolver len(products), porque reflete o que o banco realmente
    # gravou, nao o que a gente pediu.
    return len(resultado.inserted_ids)


def find_by_category(collection, category):
    """
    TODO 2:
    Busque todos os documentos da `collection` cujo campo "category"
    seja igual a `category`, ORDENADOS por "price" CRESCENTE. Retorne
    como uma lista de dicionarios, SEM o campo "_id" (use projecao para
    excluir: `{"_id": 0}`).
    """
    # A projecao {"_id": 0} exclui o ObjectId da resposta. Sem ela, cada
    # documento volta com um campo que nao existe no dominio da aplicacao
    # e que nao e serializavel em JSON sem conversao.
    cursor = collection.find(
        {"category": category},
        {"_id": 0},
    ).sort("price", ASCENDING)

    # find() devolve um CURSOR preguicoso, nao uma lista: enquanto nao for
    # consumido, nada trafega. list() materializa, que e o que o contrato
    # desta funcao pede.
    return list(cursor)


def average_price_by_category(collection):
    """
    TODO 3:
    Use o pipeline de agregacao do MongoDB (`collection.aggregate([...])`)
    para calcular o PRECO MEDIO ("price") agrupado por "category".
    Retorne um dicionario {category: preco_medio}.

    Dica: um pipeline com um unico estagio `$group` resolve:
        [{"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}]
    """
    # O $group roda DENTRO do banco: so os agregados voltam pela rede, em
    # vez de todos os documentos para somar do lado da aplicacao. E o mesmo
    # principio da localidade dos dados do Hadoop -- levar o calculo ate o
    # dado, nao o contrario.
    pipeline = [
        {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}}
    ]

    # No resultado do $group, "_id" carrega o valor pelo qual foi agrupado
    # (a categoria), nao o ObjectId do documento.
    return {
        doc["_id"]: doc["avg_price"]
        for doc in collection.aggregate(pipeline)
    }


def increment_stock(collection, product_id, delta):
    """
    TODO 4:
    Incremente (ou decremente, se `delta` for negativo) o campo "stock"
    do produto cujo "product_id" seja igual a `product_id`, usando o
    operador atomico `$inc` do MongoDB (`update_one`). Depois, busque o
    documento atualizado e retorne o NOVO valor de "stock".

    Se nenhum produto com esse `product_id` existir, retorne `None`.
    """
    filtro = {"product_id": product_id}

    # $inc soma no servidor, de forma atomica. Ler o valor, somar em Python
    # e gravar de volta abriria uma janela de "lost update": duas baixas de
    # estoque simultaneas leriam o mesmo numero e uma sobrescreveria a outra.
    resultado = collection.update_one(filtro, {"$inc": {"stock": delta}})

    # matched_count distingue "nao achei o produto" de "achei mas o valor
    # ja era esse". modified_count seria 0 nos dois casos.
    if resultado.matched_count == 0:
        return None

    # Ressalva: o $inc acima e atomico, mas a releitura abaixo e uma
    # SEGUNDA operacao. Entre as duas, outro cliente pode alterar o
    # estoque -- entao o valor devolvido reflete o estado atual do
    # documento, nao necessariamente "o resultado deste incremento".
    #
    # Em producao o certo seria find_one_and_update com
    # ReturnDocument.AFTER, que incrementa e devolve o novo valor numa
    # unica operacao atomica. Mantive update_one + find_one porque o
    # enunciado pede explicitamente essa sequencia.
    documento = collection.find_one(filtro, {"_id": 0, "stock": 1})

    return documento["stock"]
