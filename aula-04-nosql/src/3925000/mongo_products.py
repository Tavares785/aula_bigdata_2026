def insert_products(collection, products):
    result = collection.insert_many(products)
    return len(result.inserted_ids)


def find_by_category(collection, category):
    result = collection.find(
        {"category": category},
        {"_id": 0}
    ).sort("price", 1)

    return list(result)


def average_price_by_category(collection):
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