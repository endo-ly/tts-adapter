"""Domain errors for tts-adapter."""


class TTSAdapterError(Exception):
    """Base error for all tts-adapter domain errors."""


class ModelNotFoundError(TTSAdapterError):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        super().__init__(f"Model not found: {model_id}")


class VoiceNotFoundError(TTSAdapterError):
    def __init__(self, voice_id: str) -> None:
        self.voice_id = voice_id
        super().__init__(f"Voice not found: {voice_id}")


class VoiceBindingNotFoundError(TTSAdapterError):
    def __init__(self, voice_id: str, model_id: str) -> None:
        self.voice_id = voice_id
        self.model_id = model_id
        super().__init__(
            f"Voice '{voice_id}' does not support model '{model_id}'"
        )


class UnsupportedResponseFormatError(TTSAdapterError):
    def __init__(self, format: str) -> None:
        self.format = format
        super().__init__(f"Unsupported response format: {format}")


class UnsupportedSpeedError(TTSAdapterError):
    def __init__(self, speed: float) -> None:
        self.speed = speed
        super().__init__(f"Unsupported speed: {speed}")


class ProviderNotFoundError(TTSAdapterError):
    def __init__(self, provider: str) -> None:
        self.provider = provider
        super().__init__(f"Provider not found: {provider}")


class ProviderExecutionError(TTSAdapterError):
    def __init__(self, provider_name: str, detail: str) -> None:
        self.provider_name = provider_name
        self.detail = detail
        super().__init__(
            f"Provider '{provider_name}' execution failed: {detail}"
        )


class ProviderTimeoutError(TTSAdapterError):
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name
        super().__init__(f"Provider '{provider_name}' timed out")


class InvalidProfileError(TTSAdapterError):
    pass
