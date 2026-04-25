"""Resolves model + voice profiles and merges config."""

from app.domain.entities.model_profile import ModelProfile
from app.domain.entities.voice_profile import VoiceProfile
from app.domain.errors import ModelNotFoundError, VoiceBindingNotFoundError, VoiceNotFoundError
from app.domain.interfaces.model_profile_repository import ModelProfileRepository
from app.domain.interfaces.voice_profile_repository import VoiceProfileRepository
from app.application.services.option_merger import OptionMerger


class ProfileResolver:
    def __init__(
        self,
        model_repo: ModelProfileRepository,
        voice_repo: VoiceProfileRepository,
    ) -> None:
        self._model_repo = model_repo
        self._voice_repo = voice_repo

    def resolve(
        self, model_id: str, voice_id: str
    ) -> tuple[ModelProfile, VoiceProfile, dict]:
        model = self._model_repo.get_by_id(model_id)
        voice = self._voice_repo.get_by_id(voice_id)

        binding = voice.bindings.get(model_id)
        if binding is None:
            raise VoiceBindingNotFoundError(voice_id, model_id)

        config = OptionMerger.merge(
            model_defaults=model.defaults.model_dump(),
            voice_defaults=voice.defaults.model_dump(),
            model_provider_config=model.provider_config,
            voice_binding_config=binding.provider_config,
            request_options={},
        )

        return model, voice, config
