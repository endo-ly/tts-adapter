"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router
from app.api.routes.voices import router as voices_router
from app.api.routes.openai_speech import router as openai_speech_router
from app.api.routes.native_speech import router as native_speech_router
from app.application.services.option_merger import OptionMerger
from app.application.services.profile_resolver import ProfileResolver
from app.application.services.provider_registry import ProviderRegistry
from app.application.use_cases.synthesize_speech import SynthesizeSpeech
from app.infrastructure.config.settings import Settings
from app.infrastructure.providers.fake.provider import FakeProvider
from app.infrastructure.providers.irodori.provider import IrodoriProvider
from app.infrastructure.repositories.yaml_model_profile_repository import YamlModelProfileRepository
from app.infrastructure.repositories.yaml_voice_profile_repository import YamlVoiceProfileRepository

app = FastAPI(title="tts-adapter", version="0.1.0")

app.include_router(health_router)
app.include_router(models_router)
app.include_router(voices_router)
app.include_router(openai_speech_router)
app.include_router(native_speech_router)

_settings = Settings()
_model_repo = YamlModelProfileRepository(
    yaml_path=f"{_settings.assets_dir}/models/models.yaml"
)
_voice_repo = YamlVoiceProfileRepository(
    voices_dir=f"{_settings.assets_dir}/voices"
)
_provider_registry = ProviderRegistry()
_provider_registry.register(FakeProvider())
_provider_registry.register(
    IrodoriProvider(
        irodori_repo_dir=_settings.irodori_repo_dir or "",
        tmp_dir=_settings.tmp_dir,
        timeout_sec=_settings.timeout_sec,
    )
)
_profile_resolver = ProfileResolver(
    model_repo=_model_repo, voice_repo=_voice_repo
)


def get_model_repo() -> YamlModelProfileRepository:
    return _model_repo


def get_voice_repo() -> YamlVoiceProfileRepository:
    return _voice_repo


def get_synthesize_speech() -> SynthesizeSpeech:
    return SynthesizeSpeech(
        profile_resolver=_profile_resolver,
        provider_registry=_provider_registry,
        option_merger=OptionMerger(),
    )
