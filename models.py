"""Shared data model and match logic."""

from __future__ import annotations

from dataclasses import dataclass, field

import config


@dataclass
class Pet:
    source: str            # human label, e.g. "MSPCA"
    uid: str               # globally-unique, stable id, e.g. "mspca:a472692"
    name: str
    url: str
    breed: str = ""
    age: str = ""
    sex: str = ""
    location: str = ""
    weight_lb: float | None = None
    photo: str = ""

    @property
    def weight_str(self) -> str:
        if self.weight_lb is None:
            return "weight not listed"
        return f"{self.weight_lb:g} lb"


def size_guess(breed: str) -> str | None:
    """Rough size from breed text: 'small', 'large', or None if unclear."""
    b = breed.lower()
    # A large keyword wins over a small one ("terrier" in "pit bull terrier").
    if any(k in b for k in config.LARGE_BREED_KEYWORDS):
        return "large"
    if any(k in b for k in config.SMALL_BREED_KEYWORDS):
        return "small"
    return None


def is_match(pet: Pet) -> bool:
    """Does this dog meet the family's criteria?"""
    b = pet.breed.lower()
    if any(k.lower() in b for k in config.EXCLUDE_BREED_KEYWORDS):
        return False

    if pet.weight_lb is not None:
        return pet.weight_lb <= config.MAX_WEIGHT_LB

    # No published weight (e.g. ARL Boston).
    if not config.INCLUDE_UNKNOWN_WEIGHT:
        return False
    return size_guess(pet.breed) != "large"
