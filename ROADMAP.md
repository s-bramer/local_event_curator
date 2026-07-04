# Roadmap & Project Log

This is a living document: the top section is the standing roadmap (suggested upgrades, in priority order per `CLAUDE.md`), and the bottom section is a dated progress log updated as work actually happens. When an item below is implemented, move a short note to the Progress Log and mark the item done here rather than deleting it, so the history stays visible.

Architecture note (2026-07-04): reviewed whether the overall CSV-config-driven scraper → normalize/validate → publish → Flask shape needs a rewrite. Conclusion: no — it's sound for this project's scale (~20 sites, shared with friends, not commercial). The debt below is implementation-level, not structural. One open question, not yet decided: whether the 56-column flat CSV per-site config should eventually become one YAML/JSON file per site (more self-documenting, easier for a non-technical friend to help maintain) — deferred until the current format is actually causing pain, per `CLAUDE.md`'s "don't replace CSV without a compelling reason."

---

## 0. Quick, high-value bug fixes (do first — cheap, isolated)

- [ ] List mutated while iterating (`date_list.pop(index)` inside `for index, item in enumerate(date_list)`) silently skips date tokens — `date_muncher.py:99-111`. Fix: build a filtered list instead of popping from the list being iterated.
- [ ] DuckDuckGo fallback checks the **stale** Nominatim `response.status_code` instead of the new request's status, and indexes a regex match `[0]` with no guard — `address_sniffer.py:64-66`. Fix: check the new response's status; guard the index with `if matches:`.
- [ ] `sys.exit()` on "no valid method selected" kills the **entire batch run** over one bad CSV config row — `scraper_standalone.py:181,216,258,300`. Fix: raise a catchable exception instead; let the per-row loop log-and-skip.
- [ ] `logging.basicConfig(..., filemode='w')` truncates `error.log` every run — no history between runs — `scraper_standalone.py:18`. Fix: switch to `filemode='a'` (or rotate/timestamp per run, see §6).

These four are pure fixes with no behavioral ambiguity — worth one small PR on their own.

---

## 1. Reliability

- [ ] **Problem:** Errors are modeled as sentinel strings (`"ERROR: ..."`, `'XXXXXX'` tuples) checked via `"ERROR:" in x` substring tests. Bare/broad `except:` blocks throughout `get_all_events`, `get_dates`, `get_content`, `get_category`, `get_council`, `get_town`, `sniff_sniff` swallow every exception type, masking real bugs.
  **Solution:** Catch specific exceptions (`AttributeError`, `requests.RequestException`, `IndexError`) instead of bare `except:`; keep the outer per-row loop as the one place that catches-and-continues, so one site's failure never aborts the batch. Introduce this incrementally per function, not as a single sweeping rewrite.
  **Benefit:** Failures become distinguishable (network vs. parse vs. config); matches CLAUDE.md's "continue processing other sites if one fails."
  **Downside:** Touches many call sites — do it after the test harness (§8) exists, so regressions are caught.
  **Effort:** M

- [ ] **Problem:** No HTTP session reuse, no retry/backoff, a flat 100s timeout per `requests.get()`.
  **Solution:** Share one `requests.Session()` (with `HTTPAdapter`/`Retry` for transient 5xx/connection errors) across the run; lower the default timeout (~20-30s) with per-site override via CSV only where genuinely needed.
  **Benefit:** Fewer transient failures, faster runs.
  **Downside:** Session reuse changes cookie/header state across requests — check no site relies on fully independent per-request sessions.
  **Effort:** S

- [ ] **Problem:** Dead/duplicate code inflates maintenance surface: `scraper.py` (near-identical, superseded copy of `scraper_standalone.py`), `local_event_tracker/` (orphaned 2022 prototype, last git commit 2022-11-11, zero references from any root file, includes a hardcoded personal file path in a Selenium script), `API_request_check.py` (disposable one-off, never wired into the CSV pipeline).
  **Solution:** Delete `scraper.py` and `API_request_check.py`. Delete (or archive on a separate branch/tag) `local_event_tracker/` — git history preserves it if ever needed.
  **Benefit:** Removes "which scraper is actually live" confusion, shrinks the repo, removes a leaked personal path.
  **Downside:** None functionally — confirm nothing on PythonAnywhere references these paths before deleting.
  **Effort:** S

---

## 2. Date Parsing

- [ ] **Problem:** `date_muncher.munch_munch()` is a hand-rolled ~110-line tokenizer built on `calendar` + regex splitting. It cannot handle any of the CLAUDE.md-named patterns ("second Friday of every month," "Wednesdays - fortnightly," "tours run weekly/monthly," "term time only") — when it finds no day+month tokens it just logs a warning and returns a placeholder. `error.log` confirms this failing today for "Tours run weekly" / "Tours run monthly." `python-dateutil` is already a listed dependency but unused for parsing.
  **Solution:** Layer, don't rewrite: (1) keep `munch_munch` as the fast path for its already-working explicit-date cases; (2) when it returns "no date found," pass the raw string through `dateutil.parser.parse(fuzzy=True)` as a second-pass fallback; (3) for genuinely recurring/relative phrases with no fixed date, explicitly classify them (see next item) rather than forcing a parse. Only reach for `dateparser` if `dateutil` proves insufficient in practice.
  **Benefit:** Fixes real, currently-failing cases; avoids silently mislabeling recurring events as "date not found."
  **Downside:** `fuzzy=True` parsing can misfire on ambiguous text — needs a sanity-range check on the result (ties into §5 validation).
  **Effort:** M

- [ ] **Problem:** Recurring-event phrases are indistinguishable from "parsing failed" today.
  **Solution:** Add a small keyword/regex classifier (weekly/monthly/fortnightly/term time/"every <weekday>") that runs before the tokenizer; on match, short-circuit to a `recurring` status that preserves the original phrase for display and is tracked as its own bucket in the run summary.
  **Benefit:** Turns unactionable failures into correctly labeled data; feeds the run-summary metrics CLAUDE.md's scheduling section asks for.
  **Downside:** Regex-based classification will always be incomplete; expect iteration as new phrasings surface.
  **Effort:** S-M

---

## 3. Location Recognition

- [ ] **Problem:** `address_sniffer.sniff_sniff()` does an exact-string match against `addresses_db.csv`, reloading the whole CSV from disk on every call. Whitespace/case/punctuation differences cause avoidable misses that trigger live network calls.
  **Solution:** Load the CSV once per run into memory; normalize keys (strip/lower/collapse whitespace) before lookup; add `rapidfuzz` as a fuzzy-match fallback before falling through to network lookups.
  **Benefit:** Fewer unnecessary network calls, fewer near-duplicate DB rows.
  **Downside:** Fuzzy match needs a conservative similarity threshold to avoid merging two distinct venues with similar names.
  **Effort:** M

- [ ] **Problem:** Nominatim is called with no rate limiting and no compliant identifying `User-Agent` (violates its usage policy — IP-ban risk). The DuckDuckGo HTML-scrape fallback is fragile and likely already broken.
  **Solution:** Add a descriptive `User-Agent` + a ~1 req/sec throttle for Nominatim. Drop the DuckDuckGo fallback entirely; on geocoding failure, just log "location unresolved."
  **Benefit:** Removes IP-ban risk and a likely-dead code path; simplifies the failure model.
  **Downside:** Slightly lower address-resolution rate for edge cases.
  **Effort:** S

- [ ] **Problem:** `checkmypostcode.uk` scraping for council/town uses brittle CSS-class matching, caught only by a bare `except:`.
  **Solution:** Leave the approach as-is but narrow the exception handling and log distinctly when the expected selector is simply missing (site changed) vs. a network failure.
  **Effort:** S

- [ ] **Problem:** New address lookups are appended to `addresses_db.csv` via plain `to_csv` on every miss, with no locking — a latent corruption risk.
  **Solution:** Write via temp-file-then-atomic-rename, reusing the same pattern being built for the scheduled-run safe publish (§6).
  **Effort:** S

---

## 4. Extraction Strategy (layered: BS4 → JSON-LD → OpenGraph → Playwright)

- [ ] **Problem:** No JSON-LD/schema.org extraction exists anywhere, despite it being the natural, cheap middle tier between plain HTML scraping and full Playwright rendering. `events_mode` in the CSV statically pins one method per site — there's no "try cheap, escalate if needed" cascade.
  **Solution:** Add a `get_json_ld_events()`/extraction helper that parses `<script type="application/ld+json">` blocks for `schema.org/Event` fields (name, startDate, location) — likely fixes several currently-failing sites (e.g. wmc.org.uk, nationaltrust.org.uk) without launching a browser. Ship first as an opt-in `events_mode` value; the fuller automatic cascade (BS4 → JSON-LD → OpenGraph → Playwright) is a larger follow-up.
  **Benefit:** Cuts Playwright/Chromium overhead for most sites; more resilient to markup churn.
  **Downside:** Some sites' JSON-LD is incomplete/malformed — needs defensive `json.loads` handling.
  **Effort:** S (opt-in mode) → L (full auto-cascade, deliver incrementally)

- [ ] **Problem:** `render_soup()` launches a fresh Chromium instance per JS-rendered site.
  **Solution:** Once the JSON-LD tier shrinks the number of sites needing Playwright, reuse a single browser instance across the remaining `JSRender` rows within one run.
  **Effort:** S — sequence after the cascade above.

---

## 5. Validation

- [ ] **Problem:** No validation gate before writing to the consolidated CSV — missing titles, unparseable dates, malformed URLs, and duplicates can all pass straight through today.
  **Solution:** Add a `validate_event(row)` check run before output: non-empty title, parseable-or-explicitly-recurring date, well-formed URL, non-placeholder location. Hard failures (no title/URL) are dropped and logged; soft issues (unresolved location, recurring date) are kept but flagged.
  **Benefit:** Stops visibly broken rows reaching the live site; produces the per-category failure counts §6 needs.
  **Downside:** Hard-fail vs. soft-fail thresholds need tuning against real data.
  **Effort:** M

- [ ] **Problem:** Duplicate detection is currently ad hoc, exact title/location match only.
  **Solution:** Centralize: exact URL match first, then `rapidfuzz` title similarity + same-date as a second tier for cross-posted events from different sites.
  **Downside:** Fuzzy dedup risks merging two distinct same-day events with similar titles — use a conservative threshold.
  **Effort:** M

---

## 6. Logging & Scheduled Automatic Runs

- [ ] **Problem:** `logging.basicConfig(level=logging.ERROR, ...)` is hardcoded, so INFO-intent messages get logged via `logger.error()` — severities are meaningless today.
  **Solution:** Use proper levels (`.info()`/`.warning()`/`.error()`) and set the handler to `INFO`; move to per-run timestamped log files once the scheduled run below exists.
  **Effort:** S

- [ ] **Problem:** Nothing exists yet for unattended daily runs or safe publishing — a failed/partial scrape today would directly overwrite `events_database.csv`, which Flask reads live with no fallback.
  **Solution:** Add `run_scraper.py` as the PythonAnywhere scheduled-task entry point: scrape into a temp file → validate (§5) plus sanity checks (event count not wildly below previous run, duplicate rate not abnormal) → if valid, atomically replace the live CSV (`os.replace`) and keep a timestamped snapshot → if invalid, leave the previous CSV untouched, log why → always emit a run summary matching the fields CLAUDE.md lists.
  **Benefit:** Directly implements the CLAUDE.md-mandated safe-publish workflow.
  **Downside:** Needs a snapshot retention policy; confirm PythonAnywhere account tier supports the desired schedule.
  **Effort:** M

- [ ] **Problem:** `error.log` is tracked in git, adding noise on every run.
  **Solution:** Add it (and any per-run logs) to `.gitignore`; untrack the currently-committed copy.
  **Effort:** S

---

## 7. Flask App

- [ ] **Problem:** Hardcoded `app.secret_key = "your_secret_key"` and hardcoded sender/receiver email addresses.
  **Solution:** Move all three to env vars, same pattern as the existing `EMAIL_PW = os.getenv(...)`.
  **Effort:** S

- [ ] **Problem:** Every request re-reads and re-parses `events_database.csv` from disk; no server-side filtering/sorting/pagination.
  **Solution:** Cache the parsed event list in memory keyed on the CSV's mtime; add simple query-string filtering/pagination via plain Python slicing — no new framework or database.
  **Downside:** Cache invalidation must be tied to §6's atomic file replace, or it'll serve stale data until a process restart.
  **Effort:** S-M

- [ ] **Problem:** Fully commented-out dead code for a "rerun scraper from the website" feature (`task()`, `/ajaxprogressbar`, `/status`).
  **Solution:** Delete it now that §6 provides a proper unattended mechanism.
  **Effort:** S

- [ ] **Problem:** `Procfile` (`web: gunicorn main:app`) is a Heroku-style artifact that conflicts with CLAUDE.md's stated PythonAnywhere hosting.
  **Solution:** Confirm whether a Heroku deployment still exists; if not, delete it. **Open question — needs your input.**
  **Effort:** S (pending confirmation)

---

## 8. Modernization & Dependency Cleanup

- [ ] **Problem:** No type hints on most functions, no dataclasses, no `pathlib`, zero tests — and the two riskiest, bug-prone modules (`date_muncher`, `address_sniffer`) have no safety net for the refactors above.
  **Solution:** Add an `Event` dataclass at the point rows are assembled for output; add type hints opportunistically as functions are touched; add `pytest` coverage for `date_muncher.munch_munch` (explicit cases for every CLAUDE.md-listed date pattern) and `address_sniffer` (mocked network calls) **before** touching their internals in §1-§3.
  **Benefit:** Locks in current (fixed) behavior before refactoring.
  **Effort:** M initial, S ongoing

- [ ] **Problem:** `requirements.txt` pins 2022-era versions and is **missing `playwright`, `lxml`, `html5lib` entirely** — a clean install fails today.
  **Solution:** Regenerate from the actual working environment (`pip freeze`), add the three missing packages, bump versions to current stable minors (checked against PythonAnywhere's supported Python version). Drop Windows-only entries (`win-inet-pton`, `PySocks`).
  **Downside:** Version bumps carry a small regression risk — re-run the full scraper across all `events_mode` types after upgrading.
  **Effort:** S-M

- [ ] **Problem:** Repo clutter: `.~lock.event_pages.csv#`, `__pycache__/`, backup CSVs (`event_pages_doc.csv`, `event_pages_full_list_backup.csv`) committed alongside the live config.
  **Solution:** Add lock files/`__pycache__`/`*.pyc` to `.gitignore`; confirm which backup CSVs are still needed before moving/deleting.
  **Effort:** S

---

## Suggested Sequencing

1. §0 bug fixes — one small PR, no dependencies.
2. §6 logging fix + §7 env-var/secret fixes + §8 `.gitignore`/clutter — cheap, parallelizable, no design risk.
3. §8 test harness for `date_muncher`/`address_sniffer` — before touching their internals.
4. §1 reliability + §2 date parsing + §3 location — the core robustness pass, run against the new tests.
5. §4 JSON-LD extraction tier, then the fuller cascade.
6. §5 validation — needs §8's dataclass, feeds §6.
7. §6 scheduled runs / safe publish.
8. §7 Flask caching/pagination + §8 dependency version bumps — lowest urgency.

---

## Progress Log

_Newest entries at the top. One entry per work session: date, what changed, what's next._

### 2026-07-04 — Roadmap created
Full audit of the scraper pipeline, date/location parsing, Flask app, and repo structure completed. No code changed yet. Confirmed the overall architecture doesn't need a rewrite; debt is concentrated in specific modules (listed above). Added `ROADMAP.md` as the living log for tracking this work. `CLAUDE.md` updated with an access-scope instruction (repo-only, ask before touching anything outside it).
