import json
import unittest
import utils as tu

from order.app import app
from unittest.mock import patch


class OrdersTestCase(unittest.TestCase):

    def __init__(self):
        app.testing = True
        self.client = app.test_client()

    def test_remove_item_success(self):
        user = tu.create_user()
        user_id = user['user_id']

        order = tu.create_order(user_id)
        order_id = order['order_id']

        # add item to the stock service
        item = tu.create_item(10)
        item_id: str = item['item_id']

        # Mock the find item method
        with patch("requests.get") as find_item_mock:
            # Configure the mock response
            find_item_mock.return_value.status_code = 200
            find_item_mock.return_value.json.return_value = {
                "item_id": item_id,
                "price": 10
            }

            response = self.client.delete(f"/removeItem/{order_id}/{item_id}")

        # Assert the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'The item {item_id} is removed from order {order_id} successfully!')

    def test_checkout_rollback_decrease_stock(self):
        user = tu.create_user()
        user_id = user['user_id']

        order = tu.create_order(user_id)
        order_id = order['order_id']

        # add item to the stock service
        item1: dict = tu.create_item(5)
        self.assertTrue('item_id' in item1)
        item_id1: str = item1['item_id']
        stock_item1 = 10
        add_stock_response = tu.add_stock(item_id1, stock_item1)
        self.assertTrue(tu.status_code_is_success(add_stock_response))

        # add item to the stock service
        item2: dict = tu.create_item(5)
        self.assertTrue('item_id' in item2)
        item_id2: str = item2['item_id']
        stock_item2 = 1
        add_stock_response = tu.add_stock(item_id2, stock_item2)
        self.assertTrue(tu.status_code_is_success(add_stock_response))

        # add item1
        add_item_response = tu.add_item_to_order(order_id, item_id1)
        self.assertTrue(tu.status_code_is_success(add_item_response))

        # add item2
        add_item_response = tu.add_item_to_order(order_id, item_id2)
        self.assertTrue(tu.status_code_is_success(add_item_response))

        # remove stock for item2
        remove_stock_item2 = tu.subtract_stock(item_id2, stock_item2)
        self.assertTrue(tu.status_code_is_success(remove_stock_item2))

        amount = 1
        stock_after_subtract_item1 = stock_item1 - amount
        with patch("requests.post") as subtract_stock_mock1:
            subtract_stock_mock1.return_value.status_code = 200
            subtract_stock_mock1.return_value.json.return_value = \
                f"The new stock amount for item {item_id1} is {stock_after_subtract_item1}"

            response = self.client.post(f"/subtract/{item_id1}/{amount}")

            # ??????? the transaction has not finished yet
            # self.assertEqual(response.status_code, 200)
            # self.assertEqual(response.data, result)

        with patch("requests.post") as subtract_stock_mock2:
            subtract_stock_mock2.return_value.status_code = 400

            response = self.client.post(f"/subtract/{item_id2}/{amount}")
            # return Response(f"You cannot remove 1 items from a stock of 0!", status=400) # stock response

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, f"You cannot remove {amount} items from a stock of {stock_item2}!"
                         + "\nStatus of items Items were successfully returned!")

        # Check if the stock of item1 is consistent after the transaction
        stock = tu.find_item(item_id1)['stock']
        self.assertEqual(stock, stock_item1)


if __name__ == "__main__":
    unittest.main()
