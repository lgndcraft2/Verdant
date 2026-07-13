from pathlib import Path

from dotenv import load_dotenv

# The API is an application (unlike the SDK, which is a library and must not
# auto-load env files). Load the project's root .env for local/dev runs before
# settings are read. Real platform env vars take precedence — load_dotenv does
# not override values already present in the environment.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sdk.verdant.config import Settings, get_settings  # noqa: E402

__all__ = ["Settings", "get_settings"]
