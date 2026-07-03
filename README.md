# Dog Checker 🐶

Watches three Massachusetts shelter websites for newly listed **dogs under 25 lb**
and sends a **push notification** the moment a match appears — so you hear about a
dog before someone else adopts it.

Runs entirely on **GitHub Actions** (free). No server, no computer left on.

## Sites monitored

| Shelter | Weight data |
|---|---|
| [MSPCA](https://www.mspca.org/adoption-search/) (all locations) | Exact, read from each dog's profile |
| [Worcester ARL](https://worcesterarl.org/dogs-for-adoption/) | Exact, in the listing |
| [ARL Boston](https://24petconnect.com/ARLBostonAdoptablePets?at=DOG&age=A) | **Not published** — matched by breed size guess and flagged "weight not listed" |

## How it works

Every 20 minutes GitHub Actions runs `main.py`, which:

1. Scrapes each shelter for currently-listed dogs.
2. Filters to matches (see criteria in `config.py`).
3. Compares against `seen.json` — the memory of every dog seen before.
4. Sends a push notification for any **new** match.
5. Commits the updated `seen.json` back to the repo.

The first run records everything currently listed as a baseline (one summary
notification, no spam) — you're only alerted about dogs that appear *after* setup.

## One-time setup

### 1. Get push notifications with ntfy (free, no account)

1. Install the **ntfy** app ([iOS](https://apps.apple.com/us/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)).
2. Pick a **hard-to-guess topic name** (anyone who knows it can read your alerts),
   e.g. `dog-alerts-pennypacker-9f3k2`.
3. In the app: **+ → Subscribe to topic →** type that name. Have your brother and
   his girlfriend subscribe to the same topic on their phones too.

> Prefer Pushover, Discord, email, or SMS instead? You only need to rewrite the
> `send()` function in `notifier.py`.

### 2. Put this project on GitHub

```bash
cd "Dog Checker"
git init && git add . && git commit -m "Dog Checker"
gh repo create dog-checker --private --source=. --push   # or create it in the UI
```

### 3. Add your ntfy topic as a secret

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

- Name: `NTFY_TOPIC`
- Value: your topic name from step 1

(Optional `NTFY_SERVER` secret if you self-host ntfy.)

### 4. Enable the workflow

Repo → **Actions** tab → enable workflows. It now runs every 20 minutes.
Trigger the first (baseline) run yourself: **Actions → dog-check → Run workflow**.

## Tuning what counts as a match

Edit [`config.py`](config.py):

- `MAX_WEIGHT_LB` — the weight cutoff (default 25).
- `INCLUDE_UNKNOWN_WEIGHT` — alert on dogs with no published weight (ARL Boston)?
  Default `True`, minus obviously large breeds.
- `EXCLUDE_BREED_KEYWORDS` — breeds to never alert on, e.g. `["pit bull"]`.
- `LARGE_BREED_KEYWORDS` / `SMALL_BREED_KEYWORDS` — breed→size hints used only
  when a dog has no listed weight.

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py --dry-run   # scrape + print matches, never notify or save
python main.py --seed      # record current dogs as baseline, no alerts
python main.py             # real run (set NTFY_TOPIC to actually push)
```

## Notes & limitations

- **GitHub's schedule is best-effort** — a `*/20` job often runs 5–15 min late,
  and can pause after ~60 days of repo inactivity. Fine for this use; just don't
  expect to-the-second timing.
- **Actions minutes:** a run takes ~30s. On a *public* repo that's free and
  unlimited; on a *private* repo it's ~1,000 of your 2,000 free monthly minutes.
  Make the repo public, or widen the interval, if that matters.
- **ARL Boston weight** genuinely isn't in their data, so those alerts say
  "weight not listed" — glance at the breed and photo to judge size.
- If a shelter redesigns its site, its scraper in `scrapers/` may need updating;
  a failure in one site won't stop the others.
