"""Private, allowlisted Hub assets selected by the server release channel."""

from __future__ import annotations

import json
from pathlib import Path

from core.feature_access import RELEASE_CHANNELS, normalize_release_channel


_ROOT = Path(__file__).with_name("hub_release_bundles")
_ASSETS = {
    channel: {
        "manifest": (f"{channel}.manifest", "application/json; charset=utf-8"),
    }
    for channel in RELEASE_CHANNELS
}
MAX_ASSET_BYTES = 256 * 1024


def read_hub_release_asset(channel: str, asset: str = "manifest") -> tuple[bytes, str]:
    """Read only an asset explicitly registered for the resolved exact channel."""
    normalized = normalize_release_channel(channel)
    if normalized != channel or channel not in _ASSETS:
        raise ValueError("invalid release channel")
    descriptor = _ASSETS[channel].get(str(asset or ""))
    if descriptor is None:
        raise KeyError("release asset not found")
    filename, content_type = descriptor
    path = (_ROOT / filename).resolve()
    if path.parent != _ROOT.resolve():
        raise ValueError("invalid release asset path")
    payload = path.read_bytes()
    if len(payload) > MAX_ASSET_BYTES:
        raise ValueError("release asset too large")
    if asset == "manifest":
        manifest = json.loads(payload.decode("utf-8"))
        if manifest.get("schema_version") != 1 or manifest.get("channel") != channel:
            raise ValueError("invalid release manifest")
    return payload, content_type
