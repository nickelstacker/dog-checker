"""Adoption criteria and tunable settings.

Edit this file to change what counts as a match. Everything the family
cares about lives here so the rest of the code doesn't need touching.
"""

# --- Core filter ------------------------------------------------------------

# Maximum weight in pounds. Dogs with a known weight above this are skipped.
MAX_WEIGHT_LB = 25.0

# Some shelters (ARL Boston / 24petconnect) never publish a weight. When True,
# a dog with no listed weight is still alerted *unless* its breed looks clearly
# large (see LARGE_BREED_KEYWORDS). Set False to only alert on dogs whose weight
# is known and under the limit.
INCLUDE_UNKNOWN_WEIGHT = True

# Breed substrings that will exclude a dog outright (case-insensitive).
# Leave empty to allow all breeds. Example: ["pit bull", "husky"]
EXCLUDE_BREED_KEYWORDS: list[str] = []

# --- Breed size hints (used only when a weight is NOT published) ------------
# These are rough guesses to keep obvious large dogs out of the alerts for the
# Boston site. They do not affect any dog that has a real listed weight.

LARGE_BREED_KEYWORDS = [
    "shepherd", "mastiff", "cane corso", "rottweiler", "great dane", "husky",
    "malamute", "saint bernard", "st. bernard", "newfoundland", "retriever",
    "labrador", "boxer", "doberman", "akita", "pit bull", "pitbull",
    "bully", "american bulldog", "hound", "collie", "pointer", "weimaraner",
    "ridgeback", "great pyrenees", "bernese", "wolfhound", "bloodhound",
]

SMALL_BREED_KEYWORDS = [
    "chihuahua", "shih tzu", "shih-tzu", "yorkie", "yorkshire", "maltese",
    "pomeranian", "poodle", "miniature", "toy", "dachshund", "papillon",
    "havanese", "bichon", "pekingese", "pug", "terrier", "min pin",
    "pinscher", "lhasa", "corgi", "cavalier", "shiba",
]
