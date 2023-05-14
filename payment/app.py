import json
import os
import atexit
import random

from flask import Flask, Response
import redis


app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


RANDOM_SEED = 444
ID_BYTES_SIZE = 32
random.seed(RANDOM_SEED)

atexit.register(close_db_connection)


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
            "status": self.status
        }


@app.post('/create_user')
def create_user():
    # Create new user id
    new_user_id = f"user:{random.getrandbits(ID_BYTES_SIZE)}"
    while db.hget(new_user_id, "user_id"):
        new_user_id = f"user:{random.getrandbits(ID_BYTES_SIZE)}"

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
    user = db.hgetall(user_id)

    if not user:
        return Response(f"The user {user_id} does not exist in the DB!", status=404)

    return_user = {
        "user_id": user_id,
        "credit": int(user[b"credit"]),
    }
    return Response(json.dumps(return_user), mimetype="application/json", status=200)


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    amount = int(amount)
    if amount <= 0:
        return Response("The amount must be > 0!", status=400)

    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)

    try:
        new_amount = db.hincrby(user_id, "credit", amount)
    except Exception as err:
        return Response("FUND FAILED : " + str(err), status=400)

    body = {
        "done": True,
        "message": f"The new credit for user {user_id} is {new_amount}"
    }

    return Response(json.dumps(body), mimetype="application/json", status=200)


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    # Check the amount
    amount = int(amount)
    if amount <= 0:
        return Response("The amount must be > 0!", status=400)

    # Check if the user exists
    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)

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
            return Response(str(exp), status=400)
    else:
        order_payment = {
            "order_id": order_id,
            "amount": amount,
            "status": bool(order_payment[b"status"])
        }

    if order_payment["status"]:
        return Response(f"The order {order_id} has been paid already!", status=400)

    # Proceed with completing the payment
    current_credit = int(db.hget(user_id, "credit"))

    if current_credit < amount:
        return Response(f"Insufficient credit balance", status=400)

    try:
        new_credit = db.hincrby(user_id, "credit", -1 * amount)
        db.hset(order_id, "status", "True")
    except Exception as err:
        return Response(str(err), status=400)

    return Response(f"The payment of the order {order_id} is paid", status=200)


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    # Check if user exists
    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)

    # Check if the payment order exists
    if not db.hget(order_id, "order_id"):
        return Response(f"The payment for order {order_id} does not exist in the DB!", status=404)

    # Retrieve information from the database about the order payment
    order_payment = db.hgetall(order_id)
    order_payment = {
        "order_id": order_id,
        "amount": int(order_payment[b"amount"]),
        "status": bool(order_payment[b"status"])
    }

    if not order_payment["status"]:
        return Response(f"The payment for order {order_id} has been cancelled already!", status=400)

    # Invalidate the payment and reimburse the user
    try:
        new_credit = db.hincrby(user_id, "credit", order_payment["amount"])
        db.hset(order_id, "status", "False")
    except Exception as err:
        return Response(str(err), status=400)

    return Response(f"The payment of the order {order_id} has been cancelled and the current credit for user {user_id} is {new_credit}", status=200)


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    # Check if user exists
    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)

    # Check if the payment order exists
    if not db.hget(order_id, "order_id"):
        return Response(f"The payment for order {order_id} does not exist in the DB!", status=404)

    return {
        "paid": bool(db.hget(order_id, "status"))
    }
