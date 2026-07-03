"""Check every shelter, alert on new matching dogs, remember what we've seen.

Run modes:
    python main.py              normal run (alert on new matches)
    python main.py --dry-run    scrape + match, print, never send a push
    python main.py --seed       record everything as "seen" with no alerts

State lives in seen.json (committed back to the repo by the GitHub Action) so
each run only alerts on dogs that are genuinely new since last time.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import notifier
from models import Pet, is_match
from scrapers import SCRAPERS
from util import make_session

STATE_FILE = Path(__file__).with_name("seen.json")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(dry_run: bool = False, force_seed: bool = False) -> int:
    session = make_session()
    state = load_state()
    # First ever run (no state file): record the current world without spamming
    # a dozen notifications for dogs that were already listed.
    seeding = force_seed or not STATE_FILE.exists()

    new_matches: list[Pet] = []
    errors: list[str] = []

    for mod in SCRAPERS:
        try:
            pets = mod.scrape(session)
        except Exception as exc:  # one bad site shouldn't kill the others
            errors.append(f"{mod.SOURCE}: {exc}")
            print(f"ERROR scraping {mod.SOURCE}: {exc}", file=sys.stderr)
            continue

        print(f"{mod.SOURCE}: found {len(pets)} listed dog(s)")
        for pet in pets:
            if pet.uid in state:
                continue  # already known

            # On the very first run we're only recording a baseline, so skip
            # the per-dog detail fetches (e.g. 70+ MSPCA pages) we'd never alert on.
            if not seeding:
                try:
                    mod.enrich(session, pet)  # fill weight/breed where needed
                except Exception as exc:
                    print(f"  warn: enrich failed for {pet.name}: {exc}", file=sys.stderr)

            state[pet.uid] = {
                "name": pet.name, "source": pet.source, "url": pet.url,
                "weight_lb": pet.weight_lb, "first_seen": now_iso(),
            }

            if is_match(pet):
                new_matches.append(pet)
                print(f"  MATCH: {pet.name} - {pet.breed} - {pet.weight_str}")
                if not seeding and not dry_run:
                    try:
                        notifier.send(pet)
                    except Exception as exc:
                        errors.append(f"notify {pet.name}: {exc}")
                        print(f"  notify failed: {exc}", file=sys.stderr)

    if not dry_run:
        save_state(state)

    if seeding and not dry_run:
        msg = (f"Monitoring started. {len(new_matches)} matching dog(s) are "
               f"currently listed and recorded. You'll be alerted on NEW ones.")
        try:
            notifier.send_text("Dog Checker is live", msg)
        except Exception as exc:
            print(f"summary notify failed: {exc}", file=sys.stderr)

    verb = "would alert" if (dry_run or seeding) else "alerted"
    print(f"\nDone. {len(new_matches)} new match(es) {verb}. "
          f"{len(state)} dog(s) tracked total.")
    if errors:
        print(f"{len(errors)} error(s): " + "; ".join(errors), file=sys.stderr)
    # Exit non-zero only if every scraper failed, so a single flaky site
    # doesn't mark the whole Action run red.
    return 1 if len(errors) >= len(SCRAPERS) else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Adoptable dog monitor")
    ap.add_argument("--dry-run", action="store_true",
                    help="scrape and print, never send notifications or save state")
    ap.add_argument("--seed", action="store_true",
                    help="record all current dogs as seen without alerting")
    args = ap.parse_args()
    sys.exit(run(dry_run=args.dry_run, force_seed=args.seed))


if __name__ == "__main__":
    main()
