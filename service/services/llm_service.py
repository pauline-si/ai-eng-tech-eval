"""
LLM service that will handle interactions with an LLM
"""

from openai import OpenAI
from pathlib import Path
from typing import BinaryIO
from utils.shopify_utils import (
    add_order,
    remove_order,
    list_orders,
    add_product,
    remove_product,
    list_products,
)
from services.function_schemas import FUNCTION_SCHEMAS
from utils.prompt_builder import SYSTEM_PROMPT
import json

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "ChatResponse",
        "description": "A response with a message and a todo list.",
        "schema": {
            "type": "object",
            "properties": {
                "response": {"type": "string"},
                "todo_list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "status": {"type": "string"},
                            "image": {"type": "string"}  # Optional image field
                        },
                        "required": ["text", "status"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["response", "todo_list"],
            "additionalProperties": False,
        },
        # "strict": True,
    },
}


def format_list_products_response(result):
    """
    Returns a human-readable list of products from a Shopify response.
    """
    if not isinstance(result, dict) or "products" not in result:
        return f"Shopify error: {result.get('error', 'Unknown error')}"

    products = result["products"]
    if not products:
        return "There are no products in the store."

    lines = ["Latest products:"]
    for p in products:
        lines.append(f"- {p['title']} (ID: {p['id']}, Price: {p['price']})")
    return "\n".join(lines)


class OpenAILLMService:
    def __init__(
        self,
        api_key: str,
        model: str,
        tts_model: str = "tts-1",
        voice: str = "alloy",
        stt_model="gpt-4o-transcribe",
    ):
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.tts_model = tts_model
        self.voice = voice
        self.stt_model = stt_model
        self.fn_map = {
            "add_order": add_order,
            "remove_order": remove_order,
            "list_orders": list_orders,
            "add_product": add_product,
            "remove_product": remove_product,
            "list_products": list_products,
        }

    def get_response(self, prompt: str) -> dict:
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            while True:
                try:
                    # print("!!!! Sending prompt to LLM:", json.dumps(messages, indent=2))
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        functions=FUNCTION_SCHEMAS,
                        function_call="auto",
                        response_format=RESPONSE_FORMAT,
                    )

                    message = completion.choices[0].message

                except Exception as api_error:
                    print(f"Error contacting LLM: {api_error}")
                    return {
                        "response": "Seems like I have encountered an error! Please check your configuration and .env file!",
                        "todo_list": [],
                    }

                if hasattr(message, "function_call") and message.function_call:
                    func_name = message.function_call.name
                    args = json.loads(message.function_call.arguments)
                    func = self.fn_map.get(func_name)

                    if func:
                        result = func(**args)
                        if not result:
                            result = {"error": "Function returned no data."}  

                        # Special case for add_product to return todo item with image
                        if func_name == "add_product" and isinstance(result, dict):
                            product_title = result.get("title", "Unnamed Product")
                            todo_item = {
                                "text": f"Add product '{product_title}' to Shopify",
                                "status": "done",
                            }
                            if result.get("image"):
                                todo_item["image"] = result["image"]

                            messages.append(
                                {
                                    "role": "function",
                                    "name": func_name,
                                    "content": json.dumps(result),
                                }
                            )

                            return {
                                "response": f"I've added the product '{product_title}' to Shopify!",
                                "todo_list": [todo_item],
                            }
                        
                        if func_name == "list_products":
                            # print("!!!!! Raw result from list_products():", result) 
                            return {
                                "response": format_list_products_response(result),  
                                "todo_list": []
                            }                  

                        messages.append(
                            {
                                "role": "function",
                                "name": func_name,
                                "content": json.dumps(result),
                            }
                        )

                        return {
                            "response": f"Executed '{func_name}' successfully.",
                            "todo_list": []
                        }

                    else:
                        result = {"error": f"Unknown function: {func_name}"}
                        messages.append(
                            {
                                "role": "function",
                                "name": func_name,
                                "content": json.dumps(result),
                            }
                        )

                else:
                    try:
                        return json.loads(message.content)
                    except Exception:
                        return {"response": message.content, "todo_list": None}
        except Exception as e:
            return {"response": f"Error contacting LLM: {e}", "todo_list": []}

    def text_to_speech(self, text: str, output_path: Path) -> Path:
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=self.tts_model,
                voice=self.voice,
                input=text,
            ) as response:
                response.stream_to_file(output_path)
            return output_path
        except Exception as e:
            raise RuntimeError(f"Text-to-speech failed: {e}")

    def speech_to_text(self, audio_file: BinaryIO) -> str:
        try:
            transcription = self.client.audio.transcriptions.create(
                model=self.stt_model, file=audio_file, language="en"
            )
            return transcription.text
        except Exception as e:
            print(f"Error in speech_to_text: {e}")
            raise RuntimeError(f"Speech-to-text failed: {e}")
