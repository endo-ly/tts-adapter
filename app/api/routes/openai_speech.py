"""OpenAI-compatible speech synthesis route."""

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.schemas.openai_speech import OpenAISpeechRequest
from app.application.services.error_mapper import ErrorMapper
from app.application.services.option_merger import OptionMerger
from app.application.services.profile_resolver import ProfileResolver
from app.application.services.provider_registry import ProviderRegistry
from app.application.use_cases.synthesize_speech import SynthesizeSpeech
from app.domain.errors import TTSAdapterError

router = APIRouter()


@router.post("/v1/audio/speech")
async def openai_speech(req: OpenAISpeechRequest, request: Request) -> Response:
    from app.main import get_synthesize_speech
    uc = get_synthesize_speech()
    try:
        result = await uc.execute(
            model_id=req.model,
            voice_id=req.voice,
            text=req.input,
            response_format=req.response_format,
            speed=req.speed,
        )
        return Response(
            content=result.audio_bytes,
            media_type=result.media_type,
        )
    except TTSAdapterError as e:
        status, body = ErrorMapper.map(e)
        import json
        return Response(
            content=json.dumps(body),
            status_code=status,
            media_type="application/json",
        )
