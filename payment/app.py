import json
import os
import atexit
import random

from flask import Flask, Response
import redis
from pottery import Redlock

RANDOM_SEED = 444
ID_BYTES_SIZE = 32
LOCK_AUTORELEASE_TIME = 120

# Set random seed to generate unique ids for the items
random.seed(RANDOM_SEED)

app = Flask("payment-service")

# Connect to DB
db_0: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST_0'],
                                port=int(os.environ['REDIS_PORT']),
                                password=os.environ['REDIS_PASSWORD'],
                                db=int(os.environ['REDIS_DB']))

db_1: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST_1'],
                                port=int(os.environ['REDIS_PORT']),
                                password=os.environ['REDIS_PASSWORD'],
                                db=int(os.environ['REDIS_DB']))

db_2: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST_2'],
                                port=int(os.environ['REDIS_PORT']),
                                password=os.environ['REDIS_PASSWORD'],
                                db=int(os.environ['REDIS_DB']))

db_shards = [db_0, db_1, db_2]
MODULO_HASH = len(db_shards)


def close_db_connection():
    """
    Close the DB connection
    """
    for db in db_shards:
        db.close()


# Run close_db_connection function when service ends
atexit.register(close_db_connection)


# Retrieve DB from item_id
def get_db(item_id: str):
    """
    Retrieve the DB where the item_id is stored.
    :param item_id: The item id.
    :return: The db connection.
    """
    item_id_bytes = int(item_id.split(":")[1])
    db_idx = item_id_bytes % MODULO_HASH

    return db_shards[db_idx]


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credit = 0

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "credit": self.credit,
        }


class Payment:
    def __init__(self, order_id: str, amount: int, status: bool):
        self.order_id = order_id
        self.amount = amount
        self.status = status

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "amount": self.amount,
            "status": f"{self.status}"
        }


@app.post('/create_user')
def create_user():
    # Create new user id
    new_user_id = f"user:{random.getrandbits(ID_BYTES_SIZE)}"
    db = get_db(new_user_id)
    while db.hget(new_user_id, "user_id"):
        new_user_id = f"user:{random.getrandbits(ID_BYTES_SIZE)}"
        db = get_db(new_user_id)

    new_user = User(user_id=new_user_id)

    try:
        db.hset(new_user.user_id, mapping=new_user.to_dict())
    except Exception as exp:
        return Response(str(exp), status=400)

    return_user = {
        "user_id": new_user_id
    }

    return Response(json.dumps(return_user), mimetype="application/json", status=200)


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    db = get_db(user_id)

    # Lock the user
    user_lock = Redlock(key=user_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)

    if user_lock.acquire():
        user = db.hgetall(user_id)

        if not user:
            user_lock.release()
            return Response(f"The user {user_id} does not exist in the DB!", status=404)

        return_user = {
            "user_id": user_id,
            "credit": int(user[b"credit"]),
        }

        user_lock.release()
        return Response(json.dumps(return_user), mimetype="application/json", status=200)
    else:
        return Response(f"The user {user_id} is locked, try later", status=400)


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    amount = int(amount)
    if amount <= 0:
        return Response("The amount must be > 0!", status=400)
    
    db = get_db(user_id)

    user_lock = Redlock(key=user_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    if user_lock.acquire():
        if not db.hget(user_id, "user_id"):
            user_lock.release()
            return Response(f"The user {user_id} does not exist in the DB!", status=404)

        try:
            new_amount = db.hincrby(user_id, "credit", amount)
        except Exception as err:
            user_lock.release()
            return Response("FUND FAILED : " + str(err), status=400)

        body = {
            "done": True,
            "message": f"The new credit for user {user_id} is {new_amount}"
        }

        user_lock.release()
        return Response(json.dumps(body), mimetype="application/json", status=200)
    else:
        return Response(f"The user {user_id} is locked, try later", status=400)


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    # Check the amount
    amount = int(amount)
    if amount <= 0:
        return Response("The amount must be > 0!", status=400)
    
    db = get_db(user_id)

    user_lock = Redlock(key=user_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    order_lock = Redlock(key=order_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)

    if user_lock.acquire() and order_lock.acquire():
        # Check if the user exists
        if not db.hget(user_id, "user_id"):
            user_lock.release()
            order_lock.release()
            return Response(f"The user {user_id} does not exist in the DB!", status=404)

        # Check if the user has enough credit
        current_credit = int(db.hget(user_id, "credit"))
        if current_credit < amount:
            return Response(f"Insufficient credit balance", status=400)

        # Check if the orders been paid already
        order_payment = db.hgetall(order_id)

        # Create payment instance for the order if it does not exists yet
        if not order_payment:
            order_payment = Payment(
                order_id=order_id,
                amount=amount,
                status=False
            )

            try:
                db.hset(order_payment.order_id, mapping=order_payment.to_dict())
            except Exception as exp:
                user_lock.release()
                order_lock.release()
                return Response(str(exp), status=400)
        else:
            order_payment = Payment(
                order_id=order_id,
                amount=amount,
                status=order_payment[b"status"].decode("utf-8") == "True"
            )

        if order_payment.status:
            user_lock.release()
            order_lock.release()
            return Response(f"The order {order_id} has been paid already!", status=400)

        # Proceed with completing the payment
        try:
            serialized_transaction = db.pipeline()
            serialized_transaction.hincrby(user_id, "credit", -1 * amount)
            serialized_transaction.hset(order_id, "status", "True")
            serialized_transaction.execute()
        except Exception as err:
            user_lock.release()
            order_lock.release()
            return Response(str(err), status=400)
        
        user_lock.release()
        order_lock.release()
        return Response(f"The payment of the order {order_id} is paid", status=200)
    else:
        return Response(f"Not able to acquire locks for {order_id} and/or {user_id}, try later", status=400)


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    db = get_db(user_id)

    user_lock = Redlock(key=user_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    order_lock = Redlock(key=order_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)

    if user_lock.acquire() and order_lock.acquire():
        # Check if user exists
        if not db.hget(user_id, "user_id"):
            user_lock.release()
            order_lock.release()
            return Response(f"The user {user_id} does not exist in the DB!", status=404)

        # Check if the payment order exists
        if not db.hget(order_id, "order_id"):
            user_lock.release()
            order_lock.release()
            return Response(f"The payment for order {order_id} does not exist in the DB!", status=404)

        # Retrieve information from the database about the order payment
        order_payment = db.hgetall(order_id)
        order_payment = {
            "order_id": order_id,
            "amount": int(order_payment[b"amount"]),
            "status": order_payment[b"status"].decode("utf-8") == "True"
        }

        if not order_payment["status"]:
            user_lock.release()
            order_lock.release()
            return Response(f"The payment for order {order_id} has been cancelled already!", status=400)

        # Invalidate the payment and reimburse the user
        try:
            serialized_transaction = db.pipeline()
            new_credit = serialized_transaction.hincrby(user_id, "credit", order_payment["amount"])
            serialized_transaction.hset(order_id, "status", "False")
            serialized_transaction.execute()
        except Exception as err:
            user_lock.release()
            order_lock.release()    
            return Response(str(err), status=400)
        
        user_lock.release()
        order_lock.release()
        return Response(f"The payment of the order {order_id} has been cancelled and the current credit for user {user_id} is {new_credit}", status=200)
    else:
        return Response(f"Not able to acquire locks for {order_id} and/or {user_id}, try later", status=400)


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    db = get_db(user_id)
    
    user_lock = Redlock(key=user_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)
    order_lock = Redlock(key=order_id, masters={db}, auto_release_time=LOCK_AUTORELEASE_TIME)

    if user_lock.acquire() and order_lock.acquire():
        # Check if user exists
        if not db.hget(user_id, "user_id"):
            user_lock.release()
            order_lock.release()
            return Response(f"The user {user_id} does not exist in the DB!", status=404)

        # Check if the payment order exists
        if not db.hget(order_id, "order_id"):
            user_lock.release()
            order_lock.release()
            return Response(f"The payment for order {order_id} does not exist in the DB!", status=404)

        order_payment = db.hgetall(order_id)
        order_payment = {
            "order_id": order_id,
            "amount": int(order_payment[b"amount"]),
            "status": order_payment[b"status"].decode("utf-8") == "True"
        }
        user_lock.release()
        order_lock.release()
        return {
            "paid": order_payment["status"]
        }
    else:
        return Response(f"Not able to acquire locks for {order_id} and/or {user_id}, try later", status=400)
