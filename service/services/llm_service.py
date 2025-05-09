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
                        },
                        "required": ["text", "status"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["response", "todo_list"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


class OpenAILLMService:
    """
    Service class to interact with OpenAI's models for various tasks such as
    language generation (LLM), text-to-speech (TTS), and speech-to-text (STT).

    This class provides a unified interface to:
      - Generate responses from OpenAI's chat models.
      - Convert text to speech using OpenAI's TTS models.
      - Transcribe speech to text using OpenAI's STT models.
      - Dynamically call tool functions based on LLM generated tool calls.

    Attributes:
        model (str): The name of the OpenAI chat model to use (e.g., "gpt-4o").
        client (OpenAI): The OpenAI API client instance.
        tts_model (str): The TTS model to use for text-to-speech (default: "tts-1").
        voice (str): The voice to use for TTS (default: "alloy").
        fn_map (dict): Mapping of function names to callable Python functions.
        stt_model (str): The STT model to use for speech-to-text (default: "gpt-4o-transcribe").
    """

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
        self.fn_map = {
            "add_order": add_order,
            "remove_order": remove_order,
            "list_orders": list_orders,
        }
        self.stt_model = stt_model

    def get_response(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from the LLM based on the provided prompt.

        This method sends a prompt to the OpenAI chat model and handles function calling
        if the model requests it. If a function call is made, the corresponding Python
        function is executed and its result is fed back into the conversation.

        Args:
            prompt (str): The user prompt to send to the LLM.

        Returns:
            dict: A dictionary containing the LLM's response and a todo_list.
                  Example: {"response": "...", "todo_list": [...]}
                  If an error occurs, returns a dictionary with an error message.
        """
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            while True:
                try:
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
                        "response": f"Seems like I have encountered an error! Please check your configuration and .env file!",
                        "todo_list": [],
                    }

                if hasattr(message, "function_call") and message.function_call:
                    func_name = message.function_call.name
                    args = json.loads(message.function_call.arguments)
                    func = self.fn_map.get(func_name)
                    if func:
                        result = func(**args)
                    else:
                        result = {"error": f"Unknown function: {func_name}"}
                    # Add the function call and result to the message history
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
                        return {"response": message.content, "todo_list": []}
        except Exception as e:
            return f"Error contacting LLM: {e}"

    def text_to_speech(self, text: str, output_path: Path) -> Path:
        """
        Convert text to speech and save the audio to a file.

        Args:
            text (str): The text to convert to speech.
            output_path (Path): The file path where the audio will be saved.

        Returns:
            Path: The path to the saved audio file.

        Raises:
            RuntimeError: If the text-to-speech conversion fails.
        """
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=self.tts_model,
                voice=self.voice,
                input=text,
            ) as response:
                response.stream_to_file(output_path)
            return output_path
        except Exception as e:
            print(f"Error in text_to_speech: {e}")
            raise RuntimeError(f"Text-to-speech failed: {e}")

    def speech_to_text(self, audio_file: BinaryIO) -> str:
        """
        Transcribe speech from an audio file to text.

        Args:
            audio_file (BinaryIO): The audio file to transcribe.

        Returns:
            str: The transcribed text.

        Raises:
            RuntimeError: If the speech-to-text conversion fails.
        """
        try:
            transcription = self.client.audio.transcriptions.create(
                model=self.stt_model, file=audio_file, language="en"
            )
            return transcription.text
        except Exception as e:
            print(f"Error in speech_to_text: {e}")
            raise RuntimeError(f"Speech-to-text failed: {e}")
