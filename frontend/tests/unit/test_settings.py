import pytest

from config.settings import ConfigError, load_settings


def test_defaults_follow_contract():
    s = load_settings({"FLET_SECRET_KEY": "k"})
    assert (s.backend_url, s.flet_host, s.flet_port) == ("http://backend:8000", "0.0.0.0", 8001)
    assert s.upload_tmp_dir == "/tmp/uploads"
    assert s.request_timeout == 15.0
    assert s.open_browser is False


def test_secret_required_with_clear_message():
    with pytest.raises(ConfigError, match="FLET_SECRET_KEY"):
        load_settings({})
    assert load_settings({}, require_secret=False).flet_secret_key == ""


def test_backend_url_is_normalised_and_validated():
    assert load_settings({"FLET_SECRET_KEY": "k", "BACKEND_URL": " http://b:1/ "}).backend_url == "http://b:1"
    with pytest.raises(ConfigError):
        load_settings({"FLET_SECRET_KEY": "k", "BACKEND_URL": "backend:8000"})


@pytest.mark.parametrize("name,value", [("FLET_PORT", "abc"), ("FLET_PORT", "70000"),
                                        ("REQUEST_TIMEOUT", "0"), ("REQUEST_TIMEOUT", "x"),
                                        ("MAX_UPLOAD_MB", "0")])
def test_invalid_values_rejected(name, value):
    with pytest.raises(ConfigError):
        load_settings({"FLET_SECRET_KEY": "k", name: value})


def test_values_and_derived_properties():
    s = load_settings({"FLET_SECRET_KEY": "k", "REQUEST_TIMEOUT": "2.5", "MAX_UPLOAD_MB": "3",
                       "FLET_OPEN_BROWSER": "true"})
    assert s.request_timeout == 2.5 and s.max_upload_bytes == 3 * 1024 * 1024 and s.open_browser
    assert s.downloads_dir.endswith("assets/downloads")
