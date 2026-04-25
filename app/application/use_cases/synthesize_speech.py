"""Synthesize speech use case."""

from app.application.services.option_merger import OptionMerger
from app.application.services.profile_resolver import ProfileResolver
from app.application.services.provider_registry import ProviderRegistry
from app.domain.errors import UnsupportedResponseFormatError, UnsupportedSpeedError
from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult


class SynthesizeSpeech:
    def __init__(
        self,
        profile_resolver: ProfileResolver,
        provider_registry: ProviderRegistry,
        option_merger: OptionMerger,
    ) -> None:
        self._resolver = profile_resolver
        self._registry = provider_registry
        self._merger = option_merger

    async def execute(
        self,
        model_id: str,
        voice_id: str,
        text: str,
        response_format: str = "wav",
        speed: float = 1.0,
    ) -> SynthesisResult:
        if response_format != "wav":
            raise UnsupportedResponseFormatError(response_format)
        if speed != 1.0:
            raise UnsupportedSpeedError(speed)

        model, voice, merged_config = self._resolver.resolve(model_id, voice_id)

        provider = self._registry.get(model.provider)

        request = ProviderSynthesisRequest(
            model_id=model.id,
            voice_id=voice.voice_id,
            text=text,
            response_format=response_format,
            speed=speed,
            provider=model.provider,
            engine=model.engine,
            provider_config=merged_config,
        )

        return await provider.synthesize(request)
