"""Shared exceptions."""


class FolioIQError(Exception):
    """Base error for FolioIQ."""


class SpecError(FolioIQError):
    """Invalid or missing extraction spec."""


class NotImplementedPhaseError(FolioIQError):
    """Feature lands in a later phase — see PLAN.md."""
