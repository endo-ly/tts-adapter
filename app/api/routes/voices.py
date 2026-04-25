"""Voices list route."""

from fastapi import APIRouter

from app.application.use_cases.list_voices import ListVoices
from app.domain.interfaces.voice_profile_repository import VoiceProfileRepository

router = APIRouter()


def _create_list_voices(repo: VoiceProfileRepository) -> ListVoices:
    return ListVoices(voice_repo=repo)


@router.get("/v1/voices")
async def list_voices() -> dict:
    from app.main import get_voice_repo
    uc = _create_list_voices(get_voice_repo())
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
