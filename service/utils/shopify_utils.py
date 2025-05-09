"""
Functions to be used as tools for the LLM to interact with Shopify's API and a mocked development store
"""

import requests
from config import settings

HEADERS = {
    "X-Shopify-Access-Token": settings.SHOPIFY_API_ACCESS_TOKEN,
    "Content-Type": "application/json",
}
API_VERSION = settings.SHOPIFY_API_VERSION
SHOP_URL = settings.SHOPIFY_SHOP_URL


def add_order(customer_email: str, line_items: list) -> dict:
    """
    Create a new order in Shopify.
    :param customer_email: Email of the customer
    :param line_items: List of dicts, each with 'title', 'quantity', and 'price'
    """
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json"
    data = {
        "order": {
            "email": customer_email,
            "line_items": [
                {
                    "title": item["title"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                }
                for item in line_items
            ],
            "financial_status": "paid",
            "test": True,  # Mark as test order
        }
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=data, verify=False)
        resp.raise_for_status()
        order = resp.json().get("order", {})
        return {
            "order_id": order.get("id"),
            "email": order.get("email"),
            "status": order.get("fulfillment_status"),
            "line_items": [
                {"title": item["title"], "quantity": item["quantity"]}
                for item in order.get("line_items", [])
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def list_orders(limit: int = 5) -> dict:
    """
    List recent Shopify orders.
    :param limit: Number of orders to return (default 5)
    """
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json?limit={limit}"
    try:
        resp = requests.get(url, headers=HEADERS, verify=False)
        resp.raise_for_status()
        orders = resp.json().get("orders", [])
        return {
            "orders": [
                {
                    "order_id": o.get("id"),
                    "email": o.get("email"),
                    "status": o.get("fulfillment_status"),
                    "created_at": o.get("created_at"),
                    "line_items": [
                        {"title": item["title"], "quantity": item["quantity"]}
                        for item in o.get("line_items", [])
                    ],
                }
                for o in orders
            ]
        }
    except Exception as e:
        return {"error": str(e)}


def remove_order(order_id: str) -> dict:
    """
    Delete a Shopify order by order ID.
    """
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders/{order_id}.json"
    try:
        resp = requests.delete(url, headers=HEADERS, verify=False)
        if resp.status_code == 200:
            return {"order_id": order_id, "message": "Order deleted successfully."}
        else:
            return {
                "order_id": order_id,
                "error": f"Failed to delete order. Status code: {resp.status_code}, Response: {resp.text}",
            }
    except Exception as e:
        return {"error": str(e)}
