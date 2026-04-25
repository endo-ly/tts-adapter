"""Tests for OptionMerger."""

from app.application.services.option_merger import OptionMerger


class TestOptionMerger:
    def test_merge_follows_5_layer_priority(self):
        result = OptionMerger.merge(
            model_defaults={"a": "model_def", "b": "model_def", "c": "model_def", "d": "model_def", "e": "model_def"},
            voice_defaults={"a": "voice_def", "b": "voice_def", "c": "voice_def", "d": "voice_def"},
            model_provider_config={"a": "model_pc", "b": "model_pc", "c": "model_pc"},
            voice_binding_config={"a": "voice_bc", "b": "voice_bc"},
            request_options={"a": "request"},
        )
        assert result["a"] == "request"
        assert result["b"] == "voice_bc"
        assert result["c"] == "model_pc"
        assert result["d"] == "voice_def"
        assert result["e"] == "model_def"

    def test_request_overrides_win(self):
        result = OptionMerger.merge(
            model_defaults={"seed": 1},
            voice_defaults={"seed": 2},
            model_provider_config={"seed": 3},
            voice_binding_config={"seed": 4},
            request_options={"seed": 99},
        )
        assert result["seed"] == 99

    def test_binding_config_overrides_model_config(self):
        result = OptionMerger.merge(
            model_defaults={},
            voice_defaults={},
            model_provider_config={"checkpoint": "old", "device": "cpu"},
            voice_binding_config={"checkpoint": "new"},
            request_options={},
        )
        assert result["checkpoint"] == "new"
        assert result["device"] == "cpu"

    def test_empty_layers(self):
        result = OptionMerger.merge(
            model_defaults={"a": 1},
            voice_defaults={},
            model_provider_config={},
            voice_binding_config={},
            request_options={},
        )
        assert result == {"a": 1}

    def test_all_empty(self):
        result = OptionMerger.merge(
            model_defaults={},
            voice_defaults={},
            model_provider_config={},
            voice_binding_config={},
            request_options={},
        )
        assert result == {}

    def test_deep_merge_not_needed(self):
        result = OptionMerger.merge(
            model_defaults={"config": {"x": 1}},
            voice_defaults={},
            model_provider_config={},
            voice_binding_config={"config": {"y": 2}},
            request_options={},
        )
        assert result["config"] == {"y": 2}
