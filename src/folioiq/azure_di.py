"""Azure Document Intelligence OCR (requires folioiq[azure])."""

from __future__ import annotations

from typing import Protocol

from folioiq.config import FolioIQSettings
from folioiq.exceptions import FolioIQError
from folioiq.io import DocumentInput, read_document_bytes


class OCRClient(Protocol):
    def extract_text(self, document: DocumentInput) -> str:
        ...


class AzureDIClient:
    """OCR via Azure Document Intelligence prebuilt-read."""

    def __init__(self, settings: FolioIQSettings, model_id: str = "prebuilt-read") -> None:
        self.settings = settings
        self.model_id = model_id
        self._client = self._build_client()

    def _build_client(self):
        endpoint = self.settings.azure_doc_intelligence_endpoint
        key = self.settings.azure_doc_intelligence_key
        if not endpoint or not key:
            raise FolioIQError(
                "Azure Document Intelligence is not configured. "
                "Set AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY."
            )
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError as exc:
            raise FolioIQError(
                "Azure DI requires: pip install 'folioiq[azure]'"
            ) from exc

        return DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )

    def extract_text(self, document: DocumentInput) -> str:
        data, _ = read_document_bytes(document)
        poller = self._client.begin_analyze_document(
            self.model_id,
            body=data,
            content_type="application/octet-stream",
        )
        result = poller.result()
        text = (result.content or "").strip()
        if not text:
            raise FolioIQError("Azure DI returned empty OCR text")
        return text


def get_default_ocr(settings: FolioIQSettings) -> OCRClient:
    return AzureDIClient(settings)
