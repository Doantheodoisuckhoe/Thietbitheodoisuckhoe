"""Cấu hình server — đọc từ biến môi trường hoặc file .env (xem .env.example)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Mặc định SQLite cho chạy thử nhanh; triển khai thật dùng PostgreSQL:
    # postgresql+psycopg://healthwatch:matkhau@localhost:5432/healthwatch
    database_url: str = f"sqlite:///{BASE_DIR / 'healthwatch.db'}"

    jwt_secret: str = "doi-chuoi-bi-mat-nay-khi-trien-khai-that-2026"  # >= 32 ký tự
    jwt_expire_hours: int = 24 * 7
    timezone: str = "Asia/Ho_Chi_Minh"

    # Thư mục web dashboard (phục vụ tại /dashboard)
    web_dir: str = str(BASE_DIR / "web_dashboard")
    cors_origins: str = "*"

    # Push: đường dẫn file service-account JSON của Firebase. Để trống = in ra log.
    firebase_credentials: str = ""

    # SMS: "console" (in ra log) | "twilio"
    sms_provider: str = "console"
    sms_ascii: bool = True  # bỏ dấu tiếng Việt -> 160 ký tự/tin thay vì 70
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from: str = ""

    # Bộ xử lý nền
    enable_worker: bool = True
    escalation_check_s: float = 5.0
    periodic_check_s: float = 60.0
    device_offline_min: int = 30

    public_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
