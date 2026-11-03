from fastapi import APIRouter, Depends

from ..deps import CurrentUser, current_user
from ..services import weather_service

router = APIRouter(prefix="/api", tags=["shell"])


@router.get("/weather")
def weather(region: str | None = None, _: CurrentUser = Depends(current_user)):
    """WEATHER-02/03: header weather for any signed-in user; SAMPLE fallback, never stored."""
    return weather_service.get_weather(region)
