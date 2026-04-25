"""List voices use case."""

from app.domain.entities.voice_profile import VoiceProfile
from app.domain.interfaces.voice_profile_repository import VoiceProfileRepository


class ListVoices:
    def __init__(self, voice_repo: VoiceProfileRepository) -> None:
        self._repo = voice_repo

    def execute(self) -> list[VoiceProfile]:
        return self._repo.list_all()
