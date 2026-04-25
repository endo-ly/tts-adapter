"""Tests for ProviderRegistry."""

import pytest

from app.domain.errors import ProviderNotFoundError
from app.application.services.provider_registry import ProviderRegistry
from app.infrastructure.providers.fake.provider import FakeProvider


class TestProviderRegistry:
    def test_register_and_resolve(self):
        registry = ProviderRegistry()
        fake = FakeProvider()
        registry.register(fake)
        assert registry.get("fake") is fake

    def test_unknown_provider_raises(self):
        registry = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError) as exc_info:
            registry.get("nonexistent")
        assert exc_info.value.provider == "nonexistent"

    def test_register_multiple(self):
        registry = ProviderRegistry()
        fake1 = FakeProvider()
        fake1.provider_name = "alpha"
        fake2 = FakeProvider()
        fake2.provider_name = "beta"
        registry.register(fake1)
        registry.register(fake2)
        assert registry.get("alpha") is fake1
        assert registry.get("beta") is fake2

    def test_overwrite_existing(self):
        registry = ProviderRegistry()
        fake1 = FakeProvider()
        fake2 = FakeProvider()
        registry.register(fake1)
        registry.register(fake2)
        assert registry.get("fake") is fake2
