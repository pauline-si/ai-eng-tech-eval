"""
Functions used by the assistant to interact with the Shopify API.

Each function corresponds to an action GPT might trigger (add, list, or remove orders/products).
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
            "test": True,
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


def add_product(title: str, price: str, image_url: str = None) -> dict:
    """
    Add a new product to the Shopify store.
    """
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json"
    product_data = {
        "product": {
            "title": title,
            "variants": [{"price": price}],
        }
    }

    if image_url:
        product_data["product"]["images"] = [{"src": image_url}]

    try:
        resp = requests.post(url, headers=HEADERS, json=product_data, verify=False)
        resp.raise_for_status()
        product = resp.json().get("product", {})
        return {
            "id": product.get("id"),
            "title": product.get("title"),
            "price": product.get("variants", [{}])[0].get("price"),
            "image": product.get("image", {}).get("src") if product.get("image") else None,
        }
    except Exception as e:
        return {"error": str(e)}


def remove_product(product_id: str) -> dict:
    """
    Remove a product from Shopify.
    """
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products/{product_id}.json"
    try:
        resp = requests.delete(url, headers=HEADERS, verify=False)
        if resp.status_code == 200:
            return {"id": product_id, "message": "Product removed."}
        else:
            return {
                "id": product_id,
                "error": f"Delete failed. Status code: {resp.status_code}, response: {resp.text}",
            }
    except Exception as e:
        return {"error": str(e)}


def list_products(limit: int = 5) -> dict:
    try:
        limit = int(limit) # Convert limit to integer in case passed as a string
    except Exception:
        limit = 5  # Fallback if parsing fails

    """
    List recent products from Shopify.
    """
    # Added `order=created_at desc` 
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json?limit={limit}&order=created_at desc" # 
    try:
        resp = requests.get(url, headers=HEADERS, verify=False)
        resp.raise_for_status()
        products = resp.json().get("products", [])
        return {
            "products": [
                {
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "price": p.get("variants", [{}])[0].get("price"),
                    "image_url": p.get("image", {}).get("src") if p.get("image") else None,
                }
                for p in products
            ]
        }
    except Exception as e:
        return {"error": str(e)}