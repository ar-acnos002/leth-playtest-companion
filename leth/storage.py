"""Explicit storage selection; cloud mode has no filesystem fallback."""
import os


def storage_mode(configured=None):
    mode = os.environ.get("LETH_STORAGE_MODE", configured or "local")
    if mode not in ("local", "cloud"):
        raise ValueError("LETH_STORAGE_MODE must be 'local' or 'cloud'.")
    return mode
