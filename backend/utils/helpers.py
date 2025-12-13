"""Utility functions and constants for the Screen Time backend."""

from datetime import datetime, timezone
from typing import List, Tuple

DEFAULT_APP_NAME = "Total"

# Canonical set of apps exposed to the frontend dropdown.
ALLOWED_APPS: Tuple[str, ...] = (
    DEFAULT_APP_NAME,
    "YouTube",
    "TikTok",
    "Instagram",
    "Safari",
    "Chrome",
    "Messages",
    "Mail",
    "Other",
)


def current_time_utc() -> datetime:
    """Return a timezone-aware UTC timestamp.

    Returns:
        datetime: Current UTC timestamp with tzinfo.
    """

    return datetime.now(timezone.utc)


def list_allowed_apps() -> List[str]:
    """Expose the allowed screen-time apps for dropdowns.

    Returns:
        list[str]: Canonical app labels in display order.
    """

    return list(ALLOWED_APPS)


def canonicalize_app_name(raw_name: str | None) -> str:
    """Normalize a user-provided app name to the canonical list.

    Args:
        raw_name (str | None): App label supplied by the client; may be blank
            or None when the user wants to log total usage.

    Returns:
        str: Canonical app label suitable for persistence.

    Raises:
        ValueError: If the given name is not part of the allowed set.
    """

    if raw_name is None:
        return DEFAULT_APP_NAME

    candidate = str(raw_name).strip()
    if not candidate:
        return DEFAULT_APP_NAME

    lower_candidate = candidate.lower()
    for allowed in ALLOWED_APPS:
        if lower_candidate == allowed.lower():
            return allowed

    raise ValueError(
        "App name must be one of: " + ", ".join(ALLOWED_APPS)
    )


def add_api_headers(response):
    """Add standard HTTP headers to API response.

    Adds headers for content type and caching control to ensure proper
    API behavior and security.

    Args:
        response: Flask Response object to modify

    Returns:
        Response: Modified response object with added headers
    """
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response
