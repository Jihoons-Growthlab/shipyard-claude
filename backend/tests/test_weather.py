"""F02 WEATHER-T01/T02 (server): region validation, SAMPLE fallback never labelled LIVE, auth required, no DB writes."""
import pytest

from app import config
from app.services import weather_service

from .conftest import login


@pytest.fixture
def h(client):
    return login(client, "choi.qa", "qa1234")  # VIEW group: weather is shell-wide, not menu-gated


@pytest.mark.parametrize("region", ["울산", "거제", "목포"])
def test_t01_regions_sample_when_no_provider(client, h, region, monkeypatch):
    monkeypatch.setattr(config.settings, "weather_provider", "")
    r = client.get("/api/weather", params={"region": region}, headers=h)
    assert r.status_code == 200
    b = r.json()
    assert b["region"] == region and b["source"] == "SAMPLE" and b["tempC"] == weather_service.SAMPLE[region]["tempC"]
    assert b["error"]


def test_default_region_invalid_region_and_auth(client, h):
    assert client.get("/api/weather", headers=h).json()["region"] == "울산"
    r = client.get("/api/weather", params={"region": "서울"}, headers=h)
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"
    assert client.get("/api/weather", params={"region": "울산"}).status_code == 401


def test_live_only_from_successful_provider(client, h, monkeypatch):
    monkeypatch.setattr(config.settings, "weather_provider", "fake")
    monkeypatch.setitem(weather_service.PROVIDERS, "fake", lambda region: {
        "obsDt": "2026-10-19T09:00", "tempC": 20.1, "condition": "맑음", "humidity": 40, "windMs": 2.0})
    b = client.get("/api/weather", params={"region": "거제"}, headers=h).json()
    assert b["source"] == "LIVE" and b["tempC"] == 20.1 and b["obsDt"] == "2026-10-19T09:00" and b["error"] is None


@pytest.mark.parametrize("impl", [lambda r: (_ for _ in ()).throw(TimeoutError("mcp timeout")), lambda r: {"condition": "맑음"}])
def test_t02_provider_failure_falls_back_to_sample(client, h, monkeypatch, impl):
    monkeypatch.setattr(config.settings, "weather_provider", "fake")
    monkeypatch.setitem(weather_service.PROVIDERS, "fake", impl)
    b = client.get("/api/weather", params={"region": "목포"}, headers=h).json()
    assert b["source"] == "SAMPLE" and b["tempC"] == 16.2 and "mcp timeout" not in (b["error"] or "")


def test_unknown_provider_is_sample(client, h, monkeypatch):
    monkeypatch.setattr(config.settings, "weather_provider", "nope")
    assert client.get("/api/weather", headers=h).json()["source"] == "SAMPLE"
