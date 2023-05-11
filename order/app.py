import json
import os
import atexit
import random

from flask import Flask, Response
import requests
import redis

gateway_url = os.environ['GATEWAY_URL']

STOCK_SERVICE_URL = f"{gateway_url}/stock"
PAYMENT_SERVICE_URL = f"{gateway_url}/payment"

RANDOM_SEED = 42
ID_BYTES_SIZE = 32

# Set random seed to generate unique ids for the items
random.seed(RANDOM_SEED)

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


def convert_order(order):
    """
    Convert the order from bytes to proper types.

    :return: The order as a dictionary.
    """
    return {
        "order_id": order[b"order_id"].decode("utf-8"),
        "user_id": order[b"user_id"].decode("utf-8"),
        "items": json.loads(order[b"items"].decode("utf-8")),
        "paid": json.loads(order[b"paid"].decode("utf-8")),
        "total_cost": int(order[b"total_cost"])
    }


class Order:
    """
    Order class that defines the saved information in order.
    """

    def __init__(self, order_id: str, user_id: int):
        self.order_id = order_id
        self.user_id = user_id
        self.items = {}
        self.paid = False
        self.total_cost = 0

    def to_dict(self):
        """
        Convert class to dict to store in DB.

        :return: The class dictionary.
        """
        # Redis expects a dictionary of key-value pairs where the values can only be bytes, strings, integers, or floats
        # Dictionaries and booleans are not supported.
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": json.dumps(self.items),
            "paid": json.dumps(self.paid),
            "total_cost": self.total_cost
        }


@app.post('/create/<user_id>')
def create_order(user_id: str):
    """
    Create a new empty order in the DB.

    :param user_id: The id of the user who creates the order, must be >= 0.
    :return: A success response if the order has been created and saved successfully, an error otherwise.
    """
    # Create unique order id
    new_order_id = f"order:{random.getrandbits(ID_BYTES_SIZE)}"
    while db.hget(new_order_id, "order_id"):
        new_order_id = f"order:{random.getrandbits(ID_BYTES_SIZE)}"

    # Create a new order
    new_order = Order(order_id=new_order_id, user_id=user_id)

    # Store to DB
    try:
        db.hset(new_order.order_id, mapping=new_order.to_dict())
    except Exception as err:
        return Response(str(err), status=400)

    # Return success response
    return Response(json.dumps(new_order.order_id), mimetype="application/json", status=200)


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    """
    Delete the order with the given order_id.

    :param order_id: The id of the order to be deleted.
    :return: Empty successful response if successful, otherwise error.
    """
    try:
        result = db.delete(order_id)  # deletes the whole order and
                            # will return 0 if the entry does not exist
    except Exception as err:
        return Response(str(err), status=400)

        # Check if the order exists
    if not result:
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    return Response(json.dumps(f"The order with id {order_id} is removed successfully."), mimetype="application/json", status=200)


@app.get('/find/<order_id>')
def find_order(order_id):
    try:
        order = db.hgetall(order_id)  # returns dictionary
    except Exception as err:
        return Response(str(err), status=400)

    if not order:
        return Response(f"There isn't any order with {order_id} in the DB!", status=404)

    # Convert bytes to proper types
    return_order = convert_order(order)

    return Response(json.dumps(return_order), mimetype="application/json", status=200)


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    """
    Adds a given item in the given order.

    :param order_id: The id of the order.
    :param item_id:
    :return: A success response if the operation is successful, an error otherwise.
    """
    # Check if the order exists
    if not db.hget(order_id, "order_id"):
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    items = db.hget(order_id, "items")
    # Increase the field of item_id with 1 or add a new field
    items[item_id] = items.get(item_id, 0) + 1

    # Store to DB
    try:
        db.hset(order_id, "items", items) # overwrites the previous entry
    except Exception as err:
        return Response(str(err), status=400)

    return Response(f"A new item {item_id} is is added to order {order_id}", status=200)


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    """
    Removes a given item from the given order.

    :param order_id: The id of the order.
    :param item_id: The item to be removed.
    :return: A success response if the operation is successful, an error otherwise.
    """
    # Get the order
    order = db.hgetall(order_id)

    # Check if the order exists
    if not order:
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    # Convert bytes to proper types
    order = convert_order(order)

    # Check if the order is paid
    if order["paid"]:
        return Response(f"The order {order_id} is already paid!", status=400)

    # Check if the item exists in the order
    items = order["items"]
    if not items.get(item_id):
        return Response(f"The item {item_id} does not exist in order {order_id}", status=404)

    # Decrease the number of items by 1 or delete the item
    if items[item_id] > 1:
        items[item_id] -= 1
    else:
        del items[item_id]

    # Update the order
    try:
        db.hset(order_id, "items", json.dumps(items))
    except Exception as err:
        return Response(str(err), status=400)

    # Get the item from the stock
    find_item = f"{STOCK_SERVICE_URL}/find/{item_id}"
    try:
        response = requests.get(find_item)
        item = response.json()
        if response.status_code != 200:
            return Response(response.content, status=response.status_code)
    except Exception as err:
        return Response(str(err), status=404)

    # Update the total cost of the order
    try:
        db.hincrby(order_id, "total_cost", -1 * item["price"])
    except Exception as err:
        return Response(str(err), status=400)

    # Return success response
    return Response(f"The item {item_id} is removed from order {order_id} successfully!", status=200)


@app.post('/checkout/<order_id>')
def checkout(order_id):
    """
    Checks out the given order.

    :param order_id: The id of the order to be checked out.
    :return: A success response if the operation is successful, an error otherwise.
    """
    # Get the order
    order = db.hgetall(order_id)

    # Check if the order exists
    if not order:
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    # Convert bytes to proper types
    order = convert_order(order)

    # Check if the order is paid
    if order["paid"]:
        return Response(f"The order {order_id} is already paid!", status=400)

    # Check if the order is empty
    if not order["items"]:
        return Response(f"The order {order_id} is empty!", status=400)

    # Pay the order
    user_id = order["user_id"]
    pay_order = f"{PAYMENT_SERVICE_URL}/pay/{user_id}/{order_id}/{order['total_cost']}"
    try:
        response = requests.post(pay_order)
        if response.status_code != 200:
            return Response(response.content, status=response.status_code)
    except Exception as err:
        return Response(str(err), status=404)

    # Decrease the amount of stock for the items in the order
    for item_id, amount in order["items"].items():
        remove_stock = f"{STOCK_SERVICE_URL}/subtract/{item_id}/{amount}"
        try:
            response = requests.post(remove_stock)
            if response.status_code != 200:
                return Response(response.content, status=response.status_code)
        except Exception as err:
            return Response(str(err), status=404)

    # Update the order status to paid
    try:
        db.hset(order_id, "paid", json.dumps(True))
    except Exception as err:
        return Response(str(err), status=400)

    # Return success response
    return Response(f"The order {order_id} is paid successfully.", status=200)
