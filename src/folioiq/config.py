"""Environment / settings."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FolioIQSettings(BaseSettings):
    """Loads from env / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    pipeline_mode: str = "auto"

    # Azure OpenAI — matches common AZURE_* names used by billing projects
    azure_api_key: str | None = None
    azure_api_base: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "FOLIOIQ_AZURE_MODEL",
            "AZURE_OPENAI_DEPLOYMENT",
            "model",
        ),
    )

    # Azure Document Intelligence (Phase 3)
    azure_doc_intelligence_endpoint: str | None = None
    azure_doc_intelligence_key: str | None = None
