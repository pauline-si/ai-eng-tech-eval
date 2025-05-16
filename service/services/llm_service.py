"""
LLM service with hybrid memory: combines GPT for interpreting user input
and a local Python dictionary for structured memory (e.g., last added/deleted product).
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

# Shared memory outside the class to keep data between user requests
memory = {}

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
                            "image": {"type": "string"},
                        },
                        "required": ["text", "status"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["response", "todo_list"],
            "additionalProperties": False,
        },
    },
}


def format_list_products_response(result):
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
        self.message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.memory = memory  # Hybrid memory dictionary
        print("!!!! Current memory content:", self.memory)


    def get_response(self, prompt: str) -> dict:
        self.message_history.append({"role": "user", "content": prompt})

        # Handle hybrid memory queries before calling GPT
        if "what product did I just add" in prompt.lower():
            last_product = self.memory.get("last_added_product")
            if last_product:
                response = f"The last product added was '{last_product['title']}' with price ${last_product['price']} and ID {last_product['id']}."
            else:
                response = "I couldn't find a record of the last added product."
            return {"response": response, "todo_list": []}

        if "what product did i just delete" in prompt.lower():
            last_deleted = self.memory.get("last_deleted_product")
            if last_deleted:
                response = f"The last product deleted was '{last_deleted['title']}' with ID {last_deleted['id']}."
            else:
                response = "I couldn't find a record of the last deleted product."
            return {"response": response, "todo_list": []}

        # Otherwise proceed with GPT and function calling
        try:
            while True:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.message_history,
                    functions=FUNCTION_SCHEMAS,
                    function_call="auto",
                    response_format=RESPONSE_FORMAT,
                )
                message = completion.choices[0].message

                if hasattr(message, "function_call") and message.function_call:
                    func_name = message.function_call.name
                    args = json.loads(message.function_call.arguments)
                    func = self.fn_map.get(func_name)

                    if func:
                        result = func(**args) or {"error": "Function returned no data."}
                        self.message_history.append({
                            "role": "function",
                            "name": func_name,
                            "content": json.dumps(result),
                        })

                        # Store result in hybrid memory
                        if func_name == "add_product" and not result.get("error"):
                            self.memory["last_added_product"] = result

                            # Add a todo item with the image manually
                            todo_item = {
                                "text": f"Add product '{result['title']}' to Shopify",
                                "status": "done"
                            }
                            if result.get("image"):
                                todo_item["image"] = result["image"]

                            print(" !!!! Stored in memory:", self.memory["last_added_product"])

                            return {
                                "response": (
                                    f"The product '{result['title']}' with a price of ${result['price']} "
                                    f"and the specified image has been added to the store successfully."
                                ),
                                "todo_list": [todo_item]
                            }

                        elif func_name == "remove_product" and not result.get("error"):
                            self.memory["last_deleted_product"] = result

                        # Let GPT summarize other cases
                        followup = self.client.chat.completions.create(
                            model=self.model,
                            messages=self.message_history,
                            response_format=RESPONSE_FORMAT
                        )
                        reply = followup.choices[0].message
                        self.message_history.append({"role": "assistant", "content": reply.content})
                        return json.loads(reply.content)
                    else:
                        return {"response": f"Unknown function: {func_name}", "todo_list": []}

                else:
                    self.message_history.append({"role": "assistant", "content": message.content})
                    return json.loads(message.content)

        except Exception as e:
            return {"response": f"Unexpected error: {e}", "todo_list": []}

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
            raise RuntimeError(f"Speech-to-text failed: {e}")