"""F02 WEATHER-01~03 server adapter (D07). Never persisted to DB.

LIVE only when a configured provider returns data; otherwise SAMPLE with the reason (WEATHER-T02: no false LIVE).
No weather MCP server is configured in this project (.mcp.json), so no provider is registered by default and the
spec forbids inventing one. To connect a real MCP-backed provider later: register a callable in PROVIDERS and set
WEATHER_PROVIDER=<name>. A provider takes the region and returns {obsDt,tempC,condition,humidity,windMs}.
"""
import logging
from typing import Callable

from ..config import settings
from ..errors import ApiError

log = logging.getLogger(__name__)

REGIONS = ("울산", "거제", "목포")
DEFAULT_REGION = "울산"
SAMPLE = {  # mockup WX_SAMPLE (display-only values)
    "울산": {"tempC": 17.6, "condition": "맑음", "humidity": 52, "windMs": 3.2},
    "거제": {"tempC": 18.9, "condition": "구름조금", "humidity": 61, "windMs": 4.1},
    "목포": {"tempC": 16.2, "condition": "흐림", "humidity": 70, "windMs": 5.0},
}
FIELDS = ("obsDt", "tempC", "condition", "humidity", "windMs")
PROVIDERS: dict[str, Callable[[str], dict]] = {}


def get_weather(region: str | None) -> dict:
    region = region or DEFAULT_REGION
    if region not in REGIONS:
        raise ApiError(400, "VALIDATION_ERROR", "지원하지 않는 지역입니다.", {"field": "region", "allowed": list(REGIONS)})
    name = settings.weather_provider
    provider = PROVIDERS.get(name) if name else None
    if not provider:
        reason = "날씨 공급자 미설정" if not name else f"알 수 없는 날씨 공급자: {name}"
        return _sample(region, reason)
    try:
        data = provider(region)
        if not isinstance(data, dict) or data.get("tempC") is None:
            raise ValueError("응답 형식 오류")
    except Exception as e:  # provider/MCP failure must never surface as LIVE
        log.warning("weather provider %s failed for %s: %s", name, region, e)
        return _sample(region, "실시간 조회 실패")
    return {"region": region, "source": "LIVE", **{k: data.get(k) for k in FIELDS}, "error": None}


def _sample(region: str, reason: str) -> dict:
    return {"region": region, "source": "SAMPLE", "obsDt": None, **SAMPLE[region], "error": reason}
