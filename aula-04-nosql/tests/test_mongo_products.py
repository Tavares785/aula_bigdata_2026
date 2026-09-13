import os
import sys

import pytest
import mongomock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mongo_products import (
    insert_products,
    find_by_category,
    average_price_by_category,
    increment_stock,
)


@pytest.fixture
def collection():
    # mongomock implementa a mesma API do pymongo em memoria -- o codigo
    # que voce escreve aqui e IDENTICO ao que rodaria contra um MongoDB
    # de verdade, so que os testes automaticos nao precisam de Docker
    # nem de rede para rodar (o que deixa o CI rapido e confiavel).
    client = mongomock.MongoClient()
    return client.loja_db.produtos


@pytest.fixture(autouse=True)
def seeded_collection(collection):
    products = [
        {"product_id": "p1", "category": "eletronicos", "price": 1500.0, "stock": 10},
        {"product_id": "p2", "category": "eletronicos", "price": 500.0, "stock": 5},
        {"product_id": "p3", "category": "livros", "price": 40.0, "stock": 100},
        {"product_id": "p4", "category": "livros", "price": 60.0, "stock": 50},
    ]
    collection.insert_many(products)
    return collection


def test_insert_products_returns_count(collection):
    inserted = insert_products(collection, [{"product_id": "p5", "category": "moveis", "price": 300.0, "stock": 3}])
    assert inserted == 1


def test_find_by_category_returns_sorted_by_price(collection):
    result = find_by_category(collection, "eletronicos")
    prices = [doc["price"] for doc in result]
    assert prices == [500.0, 1500.0]


def test_find_by_category_excludes_mongo_id(collection):
    result = find_by_category(collection, "livros")
    assert all("_id" not in doc for doc in result)


def test_find_by_category_no_match(collection):
    result = find_by_category(collection, "brinquedos")
    assert result == []


def test_average_price_by_category(collection):
    result = average_price_by_category(collection)
    assert result == {"eletronicos": 1000.0, "livros": 50.0}


def test_increment_stock_increases(collection):
    new_stock = increment_stock(collection, "p1", 5)
    assert new_stock == 15


def test_increment_stock_decreases(collection):
    new_stock = increment_stock(collection, "p3", -20)
    assert new_stock == 80


def test_increment_stock_unknown_product_returns_none(collection):
    result = increment_stock(collection, "does-not-exist", 1)
    assert result is None
