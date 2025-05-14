from fastapi import UploadFile, File, HTTPException, APIRouter, Depends
from fastapi.responses import FileResponse
from models.chat import ChatRequest, ChatResponse, TTSRequest, STTResponse
from services.llm_service import OpenAILLMService
from utils.prompt_builder import build_prompt
from config import settings
import uuid
from pathlib import Path

router = APIRouter()


def get_llm_service():
    return OpenAILLMService(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_LLM,
        tts_model=settings.SPEECH_MODEL,
        voice=settings.VOICE,
        stt_model=settings.TRANSCRIPTION_MODEL,
    )


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, llm_service: OpenAILLMService = Depends(get_llm_service)
):
    prompt = build_prompt(request.message, request.todo_list)
    result = llm_service.get_response(prompt)

    return ChatResponse(
        response=result.get("response", ""),
        updated_todo_list = result.get("todo_list", []),
        error=result.get("error", ""),
    )


@router.post("/api/chat/audio")
async def chat_audio_endpoint(
    request: TTSRequest, llm_service: OpenAILLMService = Depends(get_llm_service)
):
    audio_filename = f"speech_{uuid.uuid4().hex}.mp3"
    audio_path = Path("/tmp") / audio_filename
    llm_service.text_to_speech(request.text, output_path=audio_path)
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename="speech.mp3",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )


@router.post("/api/chat/transcribe", response_model=STTResponse)
async def chat_transcribe_endpoint(
    audio: UploadFile = File(...),
    llm_service: OpenAILLMService = Depends(get_llm_service),
):
    # Save the uploaded file to a temporary location
    temp_path = Path("/tmp") / f"upload_{uuid.uuid4().hex}_{audio.filename}"
    with open(temp_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    try:
        with open(temp_path, "rb") as audio_file:
            transcription = llm_service.speech_to_text(audio_file)
    except Exception as e:
        print("Transcription error:", e)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        # Clean up the temp file
        temp_path.unlink(missing_ok=True)

    return {"text": transcription}