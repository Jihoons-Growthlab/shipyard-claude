import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    db_path: str = field(default_factory=lambda: os.getenv("SHIPYARD_DB_PATH", str(ROOT / "database" / "shipyard.db")))
    # No committed default secret: without APP_SECRET a per-process random key is used (tokens die on restart).
    app_secret: str = field(default_factory=lambda: os.getenv("APP_SECRET") or secrets.token_urlsafe(48))
    token_ttl: int = field(default_factory=lambda: int(os.getenv("TOKEN_TTL", "28800")))  # D04-b: 8h
    otp_token_ttl: int = field(default_factory=lambda: int(os.getenv("OTP_TOKEN_TTL", "300")))
    business_date: str = "2026-10-19"  # D06: fixed demo date
    migrations_dir: Path = ROOT / "database" / "migrations"
    # D12: PDF binaries on server filesystem, metadata (FileId/FileNm) in TB_DWG_Revision
    file_dir: str = field(default_factory=lambda: os.getenv("SHIPYARD_FILE_DIR", str(ROOT / "storage" / "drawings")))
    max_pdf_bytes: int = 30 * 1024 * 1024
    # D07: weather provider name registered in weather_service.PROVIDERS; empty => SAMPLE fallback
    weather_provider: str = field(default_factory=lambda: os.getenv("WEATHER_PROVIDER", ""))


settings = Settings()
