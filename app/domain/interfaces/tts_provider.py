"""TTSProvider interface."""

from typing import Protocol, runtime_checkable

from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult


@runtime_checkable
class TTSProvider(Protocol):
    provider_name: str

    async def synthesize(
        self,
        request: ProviderSynthesisRequest,
    ) -> SynthesisResult: ...
