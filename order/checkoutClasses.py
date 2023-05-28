import os
import requests
import json
from talepy.steps import Step

PAYMENT_SERVICE_URL = os.environ['USER_SERVICE_URL']
STOCK_SERVICE_URL = os.environ['STOCK_SERVICE_URL']


class DebitCustomerBalance(Step):

    def __init__(self, user_id, order_id, total_cost):
        self.user_id = user_id
        self.order_id = order_id
        self.total_cost = total_cost

    def execute(self, state):
        pay_order = f"{PAYMENT_SERVICE_URL}/pay/{self.user_id}/{self.order_id}/{self.total_cost}"
        response = requests.post(pay_order)
        if response.status_code != 200:
            return Exception("Failed payment")
        return state

    def compensate(self, order): # state
        return_back_money(self.user_id, self.order_id)


class RetrieveStock(Step):

    def __init__(self, requested_items):
        self.added_items = {}
        self.requested_items = requested_items

    def execute(self, state):
        for item_id, amount in self.requested_items:
            remove_stock = f"{STOCK_SERVICE_URL}/subtract/{item_id}/{amount}"
            response = requests.post(remove_stock)

            if response.status_code != 200:
                return Exception(f"Failed to add an item {item_id}")

            self.added_items[item_id] = amount
        return state

    def compensate(self, order): # state??
        return_back_added_items(self.added_items)


class UpdateOrder(Step):

    def __init__(self, order_id, db):
        self.order_id = order_id
        self.db = db

    def execute(self, state):
        self.db.hset(self.order_id, "paid", json.dumps(True))
        return state

    def compensate(self, state):  # state??
        self.db.hset(self.order_id, "paid", json.dumps(False))


def return_back_added_items(add_items) -> str:
    for item_id, amount in add_items.items():
        add_back_stock = f"{STOCK_SERVICE_URL}/add/{item_id}/{amount}"
        try:
            response = requests.post(add_back_stock)
            if response.status_code != 200:
                return f"Error when returning one of the items {item_id} " + str(response.content)
        except Exception as err:
            return "Error when returning items" + str(err)

    return "Items were successfully returned!"


def return_back_money(user_id, order_id) -> str:
    cancel_order = f"{PAYMENT_SERVICE_URL}/cancel/{user_id}/{order_id}"
    try:
        response = requests.post(cancel_order)
        if response.status_code != 200:
            return "Cancellation of payment was not successful because " + str(response.content)
    except Exception as err:
        return "Cancellation of payment was not successful " + str(err)
    return "Money were successfully returned!"

