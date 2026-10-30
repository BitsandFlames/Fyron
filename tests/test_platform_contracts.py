"""Platform boundaries exercised against the base installed wheel."""

import os

import pytest
from fyron.fhir._device_auth import _DeviceAuth, DeviceAuthError


def test_windows_cache_rejected_without_network(tmp_path, monkeypatch):
    auth = object.__new__(_DeviceAuth)
    auth.cache = tmp_path / "tokens.json"
    with monkeypatch.context() as patch:
        patch.setattr(os, "name", "nt")
        with pytest.raises(DeviceAuthError, match="POSIX"):
            with auth._cache_lock():
                raise AssertionError("Protected cache must not be entered")
    assert not auth.cache.exists()


def test_uncached_auth_is_platform_independent():
    auth = object.__new__(_DeviceAuth)
    auth.cache = None
    with auth._cache_lock():
        assert auth.cache is None
