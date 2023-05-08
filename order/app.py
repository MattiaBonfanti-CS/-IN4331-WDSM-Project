import os
import atexit
import random
import json

from flask import Flask, Response
import redis

from payment.app import remove_credit

gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


class Order:
    """
    Order class that defines the saved information in order.
    """

    def __init__(self, user_id: int):
        self.order_id = f"order:{random.getrandbits(32)}"
        self.user_id = user_id
        self.items = {}
        self.paid = False
        self.total_cost = 0

    def to_dict(self):
        """
        Convert class to dict to store in DB.

        :return: The class dictionary.
        """
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": self.items,
            "paid": self.paid,
            "total_cost": self.total_cost
        }


@app.post('/create/<user_id>')
def create_order(user_id):
    """
    Create a new empty order in the DB.

    :param user_id: The id of the user who creates the order, must be >= 0.
    :return: A success response if the order has been created and saved successfully, an error otherwise.
    """
    user_id = int(user_id)
    if user_id < 0:
        return Response("The user id can not be negative number!", status=400)

    new_order = Order(user_id=user_id)

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
        db.delete(order_id)  # deletes the whole order and
                            # will return 0 if the entry does not exist
    except Exception as err:
        return Response(str(err), status=400)

    return Response(json.dumps(""), mimetype="application/json", status=200)


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    """
    Adds a given item in the given order.

    :param order_id: The id of the order.
    :param item_id:
    :return: A success response if the operation is successful, an error otherwise.
    """

    if not db.hget(order_id, "order_id"):
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    items = db.hget(order_id, "items")
    # Increase the field of item_id with 1 or add a new field
    items[item_id] = items.get(item_id, 0) + 1

    try:
        db.hset(order_id, "items", items) # overwrites the previous entry
    except Exception as err:
        return Response(str(err), status=400)

    return Response(f"A new item {item_id} is is added to order {order_id}", status=200)


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    pass


@app.get('/find/<order_id>')
def find_order(order_id):
    try:
        order = db.hgetall(order_id) # returns dictionary
    except Exception as err:
        return Response(str(err), status=400)

    if not order:
        return Response(f"There isn't any order with {order_id} in the DB!", status=200)
    return Response(json.dumps(order), mimetype="application/json", status=200)

# def retrieve_order(order_id):
#     try:
#         order = db.hgetall(order_id) # returns dictionary
#     except Exception as err:
#         return Response(str(err), status=400)


@app.post('/checkout/<order_id>')
def checkout(order_id):
    # try:
    #     order = db.hgetall(order_id)  # returns dictionary # check..
    # except Exception as err:
    #     return Response(str(err), status=400)
    #
    # remove_credit(order.user_id, order.order_id, order.total_cost)
    pass
