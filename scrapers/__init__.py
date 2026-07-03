"""Registry of scraper modules.

Each module exposes:
    SOURCE: str
    scrape(session) -> list[Pet]          # cheap listing fetch
    enrich(session, pet) -> None          # fill in weight etc. (may be no-op)
"""

from . import arlboston, mspca, worcester

SCRAPERS = [mspca, worcester, arlboston]
