"""Push notifications via ntfy (https://ntfy.sh).

Set two environment variables:
    NTFY_TOPIC   the topic name you subscribe to in the ntfy app (required)
    NTFY_SERVER  optional, defaults to https://ntfy.sh

If NTFY_TOPIC is unset, alerts are printed to the console only (handy for
local testing). Swapping to Pushover/Discord/email means rewriting only the
`send()` function here.
"""

from __future__ import annotations

import os

import requests

from models import Pet

SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
TOPIC = os.environ.get("NTFY_TOPIC", "").strip()


def _body(pet: Pet) -> str:
    lines = [
        f"{pet.breed or 'Unknown breed'} - {pet.weight_str}",
        f"Age: {pet.age or 'unknown'}   Sex: {pet.sex or 'unknown'}",
        f"At: {pet.location or pet.source}",
    ]
    return "\n".join(lines)


def send(pet: Pet) -> None:
    title = f"New dog: {pet.name} ({pet.source})"
    if not TOPIC:
        print(f"[no NTFY_TOPIC] would notify -> {title}\n{_body(pet)}\n{pet.url}")
        return

    headers = {
        "Title": title.encode("utf-8"),
        "Click": pet.url,
        "Tags": "dog",
    }
    if pet.photo.startswith("http"):
        headers["Attach"] = pet.photo

    body = f"{_body(pet)}\n{pet.url}"
    r = requests.post(f"{SERVER}/{TOPIC}", data=body.encode("utf-8"),
                      headers=headers, timeout=20)
    r.raise_for_status()


def send_text(title: str, message: str) -> None:
    """A plain informational push (used for the first-run summary)."""
    if not TOPIC:
        print(f"[no NTFY_TOPIC] {title}: {message}")
        return
    r = requests.post(f"{SERVER}/{TOPIC}", data=message.encode("utf-8"),
                      headers={"Title": title.encode("utf-8"), "Tags": "dog"},
                      timeout=20)
    r.raise_for_status()
