import os
import atexit

from flask import Flask, Response
import redis
import requests
import json
import random

app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))

def close_db_connection():
    db.close()

order_url = os.environ['GATEWAY_URL'] + "/orders/"
stock_url = os.environ['GATEWAY_URL'] + "/stock/"

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
            "user_id" : self.user_id,
            "credit" : self.credit,
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
        "user_id" : new_user_id,
        "credit" : 0,
    }

    return Response(json.dumps(return_user), mimetype="application/json", status=200)


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    
    user = db.hgetall(user_id)

    if not user:
        return Response(f"The user {user_id} does not exist in the DB!", status=404)
    
    return_user = {
        "user_id" : user_id,
        "credit" : int(user[b"credit"]),
    }
    return Response(json.dumps(return_user), mimetype="application/json", status=200)


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    
    if int(amount) <= 0:
        body = {
            "done" : False
        }
        return Response(json.dumps(body), mimetype="application/json", status=200)

    if not db.hget(user_id, "user_id"):
        body = {
            "done" : False
        }
        return Response(json.dumps(body), mimetype="application/json", status=200)

    try:
        new_amount = db.hincrby(user_id, "credit", int(amount))
    except Exception as err:
        return Response("FUND FAILD : " + str(err), status=400)

    body = {
        "done" : True
    }

    return Response(json.dumps(body), mimetype="application/json", status=200)

@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    
    if int(amount) <= 0:
        return Response("The amount must be >0!", status=400)

    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)

    order_find_path = order_url + "find/{order_id}"
    r = requests.get(order_find_path)
    response_json = json.load(r.json())

    if r.status_code==404:
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    if bool(response_json["paid"]):
        return Response(f"The order {order_id} has been already paid", status=400)

    current_credit = int(db.hget(user_id, "credit"))

    if current_credit < int(amount):
        return Response(f"Insufficient credit balance")

    try:
        new_credit = db.hincrby(user_id, "credit", -1*int(amount))
    except Exception as err:
        return Response(str(err), status=400)

    return Response(f"The payment of the order {order_id} is paid", status=200)

@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)
    
    order_find_path = order_url + "find/{order_id}"
    r = requests.get(order_find_path)
    response_json = json.load(r.json())

    if r.status_code==404:
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    if not bool(response_json["paid"]):
        return Response(f"The payment of the order {order_id} has not been made yet", status=400)

    # Add item back to stock
    item_list = response_json["items"]

    for i in item_list:
        try:
            stock_add_path = stock_url + "add/{i}/1"
            requests.post(stock_add_path)
        except Exception as err:
            return Response(str(err), status=400)

    # Refund
    refund_amount = int(response_json["total_cost"])
    try:
        db.hincrby(user_id, "credit", refund_amount)
    except Exception as err:
        return Response(str(err), status=400)

    return Response(f"The order {order_id} is canceled successfully!", status=200)

@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    
    if not db.hget(user_id, "user_id"):
        return Response(f"The user {user_id} does not exist in the DB!", status=404)
    
    order_find_path = order_url + "find/{order_id}"
    r = requests.get(order_find_path)
    response_json = json.load(r.json())

    if r.status_code==404:
        return Response(f"The order {order_id} does not exist in the DB!", status=404)

    body = {
        "paid" : bool(response_json["paid"])
    }

    return Response(json.dumps(body), mimetype="application/json", status=200)

