"""VoiceProfileRepository interface."""

from typing import Protocol, runtime_checkable

from app.domain.entities.voice_profile import VoiceProfile


@runtime_checkable
class VoiceProfileRepository(Protocol):
    async def get_by_id(self, voice_id: str) -> VoiceProfile: ...
    async def list_all(self) -> list[VoiceProfile]: ...
