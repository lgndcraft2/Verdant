from __future__ import annotations


class VerdantError(RuntimeError):
    """Base class for VERDANT pipeline errors."""


class ProviderUnavailableError(VerdantError):
    """Raised when no provider model (Claude/Gemini) could complete a stage.

    VERDANT no longer falls back to canned heuristic output — a stage that needs a
    language model either produces a real model result or fails loudly with this
    error, so a degraded response is never mistaken for genuine analysis.
    """
