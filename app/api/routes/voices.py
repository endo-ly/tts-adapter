"""Voices list route."""

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_voice_repo
from app.application.use_cases.list_voices import ListVoices
from app.infrastructure.repositories.yaml_voice_profile_repository import YamlVoiceProfileRepository

router = APIRouter()


@router.get("/v1/voices")
async def list_voices(
    request: Request,
    repo: YamlVoiceProfileRepository = Depends(get_voice_repo),
) -> dict:
    uc = ListVoices(voice_repo=repo)
    voices = uc.execute()
    return {
        "object": "list",
        "data": [
            {
                "id": v.voice_id,
                "object": "voice",
                "display_name": v.display_name,
                "preferred_model": v.defaults.preferred_model,
            }
            for v in voices
        ],
    }
