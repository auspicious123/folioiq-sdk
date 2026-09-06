"""Azure OpenAI structured extraction (requires folioiq[azure])."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from folioiq.config import FolioIQSettings
from folioiq.exceptions import FolioIQError


class LLMClient(Protocol):
    def extract(self, *, system: str, user: str, model: type[BaseModel]) -> BaseModel:
        ...


class AzureOpenAIClient:
    """Thin wrapper around LangChain AzureChatOpenAI + structured output."""

    def __init__(self, settings: FolioIQSettings) -> None:
        self.settings = settings
        self._llm = self._build_llm()

    def _build_llm(self) -> Any:
        missing = [
            name
            for name, value in [
                ("AZURE_API_KEY", self.settings.azure_api_key),
                ("AZURE_API_BASE", self.settings.azure_api_base),
                ("AZURE_API_VERSION", self.settings.azure_api_version),
                ("model / AZURE_OPENAI_DEPLOYMENT", self.settings.azure_deployment),
            ]
            if not value
        ]
        if missing:
            raise FolioIQError(
                "Azure OpenAI is not configured. Missing: "
                + ", ".join(missing)
                + ". Set env vars or install/configure folioiq[azure]."
            )

        try:
            from langchain_openai import AzureChatOpenAI
        except ImportError as exc:
            raise FolioIQError(
                "Azure OpenAI client requires: pip install 'folioiq[azure]'"
            ) from exc

        deployment = self.settings.azure_deployment or ""
        deployment = deployment.replace("azure/", "")

        return AzureChatOpenAI(
            api_key=self.settings.azure_api_key,
            api_version=self.settings.azure_api_version,
            azure_endpoint=self.settings.azure_api_base,
            azure_deployment=deployment,
            model=deployment,
        )

    def extract(self, *, system: str, user: str, model: type[BaseModel]) -> BaseModel:
        from langchain_core.messages import HumanMessage, SystemMessage

        structured = self._llm.with_structured_output(model)
        result = structured.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=user),
            ]
        )
        if result is None:
            raise FolioIQError("LLM returned empty structured output")
        if isinstance(result, model):
            return result
        # Some versions return a dict
        return model.model_validate(result)


def get_default_llm(settings: FolioIQSettings) -> LLMClient:
    return AzureOpenAIClient(settings)
