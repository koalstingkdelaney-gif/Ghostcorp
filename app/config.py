"""Configuration from environment. No secrets in code or Git.

Defaults enforce the brief's hard rules: $0 paid spend before revenue,
outbound calling/SMS disabled, payments disabled until the owner finishes
provider onboarding in the provider's own dashboard.
"""
import os
from dataclasses import dataclass


def _flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    db_path: str = os.environ.get("AGENCY_DB_PATH", "data/agency.db")
    spend_cap_usd: float = float(os.environ.get("AGENCY_SPEND_CAP_USD", "0"))
    paused: bool = _flag("AGENCY_PAUSED")
    payments_mode: str = os.environ.get("PAYMENTS_MODE", "disabled")  # disabled|test|live
    calling_enabled: bool = _flag("CALLING_ENABLED")
    sms_enabled: bool = _flag("SMS_ENABLED")
    existing_leads_path: str = os.environ.get("EXISTING_LEADS_PATH", "")
    existing_optouts_path: str = os.environ.get("EXISTING_OPTOUTS_PATH", "")


def load_settings() -> Settings:
    return Settings(
        db_path=os.environ.get("AGENCY_DB_PATH", "data/agency.db"),
        spend_cap_usd=float(os.environ.get("AGENCY_SPEND_CAP_USD", "0")),
        paused=_flag("AGENCY_PAUSED"),
        payments_mode=os.environ.get("PAYMENTS_MODE", "disabled"),
        calling_enabled=_flag("CALLING_ENABLED"),
        sms_enabled=_flag("SMS_ENABLED"),
        existing_leads_path=os.environ.get("EXISTING_LEADS_PATH", ""),
        existing_optouts_path=os.environ.get("EXISTING_OPTOUTS_PATH", ""),
    )
