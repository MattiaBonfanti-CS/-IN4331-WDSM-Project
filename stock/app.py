import json
import os
import atexit
import random

from flask import Flask, Response
import redis
from pottery import Redlock

RANDOM_SEED = 444
ID_BYTES_SIZE = 32
LOCK_AUTORELEASE_TIME = 0.1

# Set random seed to generate unique ids for the items
random.seed(RANDOM_SEED)

# Initialize Flask app
app = Flask("stock-service")

# Connect to DB
db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    """
    Close the DB connection
    """
    db.close()


# Run close_db_connection function when service ends
atexit.register(close_db_connection)


# Define models
class Item:
    """
    Item class to define items in stock.
    """
    def __init__(self, item_id: str, price: int):
        self.item_id = item_id
        self.price = price
        self.stock = 0

    def to_dict(self):
        """
        Convert class to dict to store in DB.

        :return: The class dictionary.
        """
        return {
            "item_id": self.item_id,
            "price": self.price,
            "stock": self.stock,
        }


@app.post('/item/create/<price>')
def create_item(price: int):
    """
    Create a new item in the DB.

    :param price: The item price, must be >= 0.
    :return: A success response if the item has been saved successfully, an error otherwise.
    """
    price = int(price)
    if price < 0:
        return Response("The price must be >= 0!", status=400)

    # Create unique item id
    new_item_id = f"item:{random.getrandbits(ID_BYTES_SIZE)}"
    while db.hget(new_item_id, "item_id"):
        new_item_id = f"item:{random.getrandbits(ID_BYTES_SIZE)}"

    # Create new item
    new_item = Item(item_id=new_item_id, price=price)

    # Store to DB
    try:
        db.hset(new_item.item_id, mapping=new_item.to_dict())
    except Exception as err:
        return Response(str(err), status=400)

    # Return success response
    return_item = {
        "item_id": new_item.item_id
    }

    return Response(json.dumps(return_item), mimetype="application/json", status=200)


@app.get('/find/<item_id>')
def find_item(item_id: str):
    """
    Retrieve item from DB.

    :param item_id: The item unique id.
    :return: The retrieved item. An error otherwise.
    """
    # Lock the item
    item_lock = Redlock(key=item_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    if item_lock.acquire():
        item = db.hgetall(item_id)

        if not item:
            # Release the lock
            item_lock.release()
            return Response(f"The item {item_id} does not exist in the DB!", status=404)

        # Convert bytes to proper types
        return_item = {
            "price": int(item[b"price"]),
            "stock": int(item[b"stock"]),
        }

        # Release the lock
        item_lock.release()

        return Response(json.dumps(return_item), mimetype="application/json", status=200)
    else:
        return Response(f"The item {item_id} is locked, try later", status=400)


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    """
    Increase the stock of an item by the given amount.

    :param item_id: The item unique id.
    :param amount: The amount to add to the stock. It must be > 0.
    :return: A success response if the operation is successful, an error otherwise.
    """
    amount = int(amount)
    if amount <= 0:
        return Response("The amount must be > 0!", status=400)

    # Lock the item
    item_lock = Redlock(key=item_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    if item_lock.acquire():
        if not db.hget(item_id, "item_id"):
            # Release the lock
            item_lock.release()
            return Response(f"The item {item_id} does not exist in the DB!", status=404)

        # Increase the stock amount of the item
        try:
            new_amount = db.hincrby(item_id, "stock", amount)
        except Exception as err:
            # Release the lock
            item_lock.release()
            return Response(str(err), status=400)

        # Release the lock
        item_lock.release()

        return Response(f"The new stock amount for item {item_id} is {new_amount}", status=200)
    else:
        return Response(f"The item {item_id} is locked, try later", status=400)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    """
    Decrease the stock of an item by the given amount.

    :param item_id: The item unique id.
    :param amount: The amount to subtract to the stock. It must be > 0 and <= current stock.
    :return: A success response if the operation is successful, an error otherwise.
    """
    amount = int(amount)
    if amount <= 0:
        return Response("The amount must be > 0!", status=400)

    # Lock the item
    item_lock = Redlock(key=item_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    if item_lock.acquire():
        if not db.hget(item_id, "item_id"):
            # Release the lock
            item_lock.release()
            return Response(f"The item {item_id} does not exist in the DB!", status=404)

        # Check if the amount is greater than the items in stock
        current_amount = int(db.hget(item_id, "stock"))

        if amount > current_amount:
            # Release the lock
            item_lock.release()
            return Response(f"You cannot remove {amount} items from a stock of {current_amount}!", status=400)

        # Remove the amount from the stock
        try:
            new_amount = db.hincrby(item_id, "stock", -1 * amount)
        except Exception as err:
            # Release the lock
            item_lock.release()
            return Response(str(err), status=400)

        # Release the lock
        item_lock.release()

        return Response(f"The new stock amount for item {item_id} is {new_amount}", status=200)
    else:
        return Response(f"The item {item_id} is locked, try later", status=400)
