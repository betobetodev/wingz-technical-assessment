from django.conf import settings


def test_placeholder():
    assert True


def test_settings_loaded():
    assert settings.SECRET_KEY is not None
