"""Shared setup for the test scripts.

The test scripts act as an API client (like a mobile app), so they opt in to receiving tokens
in the response body with `X-Auth-Mode: bearer` instead of browser-only HttpOnly cookies."""
import requests

_post = requests.post


def _post_with_bearer_mode(url, *args, **kwargs):
    if "/api/auth/" in url:
        kwargs["headers"] = {**(kwargs.get("headers") or {}), "X-Auth-Mode": "bearer"}
    return _post(url, *args, **kwargs)


requests.post = _post_with_bearer_mode
