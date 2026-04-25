"""Merges configuration from 5 layers in priority order."""


class OptionMerger:
    @staticmethod
    def merge(
        model_defaults: dict,
        voice_defaults: dict,
        model_provider_config: dict,
        voice_binding_config: dict,
        request_options: dict,
    ) -> dict:
        result: dict = {}
        result.update(model_defaults)
        result.update(voice_defaults)
        result.update(model_provider_config)
        result.update(voice_binding_config)
        result.update(request_options)
        return result
