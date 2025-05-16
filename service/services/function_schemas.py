"""
Function schemas for LLM with function-calling capabilities
"""

SHOPIFY_FUNCTION_SCHEMAS = [
    {
        "name": "add_order",
        "description": "Create a new order in Shopify.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_email": {
                    "type": "string",
                    "description": "The email address of the customer.",
                },
                "line_items": {
                    "type": "array",
                    "description": "A list of items to order. Each item must have a title, quantity, and price.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The name of the product.",
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "The quantity of the product.",
                            },
                            "price": {
                                "type": "number",
                                "description": "The price of the product.",
                            },
                        },
                        "required": ["title", "quantity", "price"],
                    },
                },
            },
            "required": ["customer_email", "line_items"],
        },
    },
    {
        "name": "remove_order",
        "description": "Delete a Shopify order by order ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The Shopify order ID to delete.",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_orders",
        "description": "List recent Shopify orders.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "The number of orders to return (default 5).",
                }
            },
            "required": [],
        },
    },
    {
        "name": "list_products",
        "description": "List products from the Shopify store and return a human-readable list of product titles and prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of products to list, e.g., 3 or 10."
                }
            },
            "required": []  
        },
    },
    {
        "name": "add_product",
        "description": "Add a new product to the Shopify store.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "price": {"type": "string"},
                "image_url": {"type": "string"},
            },
            "required": ["title", "price"]
        },
    },
    {
        "name": "remove_product",
        "description": "Remove a product from Shopify using its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The ID of the product to remove" # Added this description
                }
            },
            "required": ["product_id"]
        }
    }
]

FUNCTION_SCHEMAS = SHOPIFY_FUNCTION_SCHEMAS
