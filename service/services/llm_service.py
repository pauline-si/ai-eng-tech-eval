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
from utils.prompt_builder import SYSTEM_PROMPT, build_prompt
import json

# Shared memory and message history outside the class to keep data between user requests
memory = {}
message_history = [{"role": "system", "content": SYSTEM_PROMPT}]

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

class OpenAILLMService:
    def __init__(self, api_key: str, model: str,
                 tts_model: str = "tts-1",
                 voice: str = "alloy",
                 stt_model: str = "gpt-4o-transcribe"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.tts_model = tts_model
        self.voice = voice
        self.stt_model = stt_model
        self.message_history = message_history
        self.memory = memory

         # Maps function names from OpenAI to actual Python functions
        self.fn_map = {
            "add_order": add_order,
            "remove_order": remove_order,
            "list_orders": list_orders,
            "add_product": add_product,
            "remove_product": remove_product,
            "list_products": list_products,
        }

    def get_response(self, user_message: str) -> dict:
        prompt = build_prompt(user_message, todo_list=[], memory=self.memory)
        self.message_history.append({"role": "user", "content": prompt})

        #print("\n Current message history:")
        #for i, msg in enumerate(self.message_history):
            #print(f"{i+1}. {msg}")

        try:
            while True:
                # Ask GPT to reply or call a function if needed
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.message_history,
                    functions=FUNCTION_SCHEMAS,
                    function_call="auto",  # GPT decide if it should call a function or just respond
                    response_format=RESPONSE_FORMAT,
                )
                message = completion.choices[0].message #Take GPT's first reply

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

                        # Store in memory and send as todo
                        if func_name == "add_product" and not result.get("error"):
                            self.memory["last_added_product"] = result
                            print("!!!!!Stored in memory:", result)

                            todo_item = {
                                "text": f"Add product '{result['title']}' to Shopify",
                                "status": "done"
                            }
                            if result.get("image"):
                                todo_item["image"] = result["image"]

                            return {
                                "response": (
                                    f"The product '{result['title']}' with a price of ${result['price']} "
                                    f"and the specified image has been added to the store successfully."
                                ),
                                "todo_list": [todo_item]
                            }
                        
                        # Store in memory
                        elif func_name == "remove_product" and not result.get("error"):
                            self.memory["last_deleted_product"] = result

                        # Send function result back to GPT for final user response    
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
                    
                # If no function used, just return a reply
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