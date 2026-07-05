# Roadmap & Project Log

This is a living document: the top section is the standing roadmap (suggested upgrades, in priority order per `CLAUDE.md`), and the bottom section is a dated progress log updated as work actually happens. When an item below is implemented, move a short note to the Progress Log and mark the item done here rather than deleting it, so the history stays visible.

Architecture note (2026-07-04): reviewed whether the overall CSV-config-driven scraper → normalize/validate → publish → Flask shape needs a rewrite. Conclusion: no — it's sound for this project's scale (~20 sites, shared with friends, not commercial). The debt below is implementation-level, not structural. One open question, not yet decided: whether the 56-column flat CSV per-site config should eventually become one YAML/JSON file per site (more self-documenting, easier for a non-technical friend to help maintain) — deferred until the current format is actually causing pain, per `CLAUDE.md`'s "don't replace CSV without a compelling reason."

---

## 0. Quick, high-value bug fixes (do first — cheap, isolated)

- [x] List mutated while iterating (`date_list.pop(index)` inside `for index, item in enumerate(date_list)`) silently skips date tokens — `date_muncher.py:99-111`. Fix: build a filtered list instead of popping from the list being iterated. **Done 2026-07-04** — rewrote the loop to `continue` instead of mutating; verified against sample date strings including the trailing-comment path that originally triggered the bug.
- [x] DuckDuckGo fallback checks the **stale** Nominatim `response.status_code` instead of the new request's status, and indexes a regex match `[0]` with no guard — `address_sniffer.py:64-66`. Fix: check the new response's status; guard the index with `if matches:`. **Done 2026-07-04.**
- [x] `sys.exit()` on "no valid method selected" kills the **entire batch run** over one bad CSV config row — `scraper_standalone.py:181,216,258,300`. Fix: raise a catchable exception instead; let the per-row loop log-and-skip. **Done 2026-07-04** — now raises `ValueError`, caught per-site in the main loop.
- [x] `logging.basicConfig(..., filemode='w')` truncates `error.log` every run — no history between runs — `scraper_standalone.py:18`. Fix: switch to `filemode='a'` (or rotate/timestamp per run, see §6). **Done 2026-07-04.**

These four are pure fixes with no behavioral ambiguity — worth one small PR on their own.

---

## 1. Reliability

- [x] **Problem:** Errors are modeled as sentinel strings (`"ERROR: ..."`, `'XXXXXX'` tuples) checked via `"ERROR:" in x` substring tests. Bare/broad `except:` blocks throughout `get_all_events`, `get_dates`, `get_content`, `get_category`, `get_council`, `get_town`, `sniff_sniff` swallow every exception type, masking real bugs.
  **Solution:** Catch specific exceptions (`AttributeError`, `requests.RequestException`, `IndexError`) instead of bare `except:`; keep the outer per-row loop as the one place that catches-and-continues, so one site's failure never aborts the batch. Introduce this incrementally per function, not as a single sweeping rewrite.
  **Benefit:** Failures become distinguishable (network vs. parse vs. config); matches CLAUDE.md's "continue processing other sites if one fails."
  **Downside:** Touches many call sites — do it after the test harness (§8) exists, so regressions are caught.
  **Effort:** M
  **Done 2026-07-04** — narrowed every bare except in both files to realistic exception tuples; also added a try/except around each event's field extraction in `run_scraper` (not just around the page fetch), since narrowing the excepts meant an unanticipated error could otherwise propagate and abort the rest of that site's events instead of just that one event.

- [x] **Problem:** No HTTP session reuse, no retry/backoff, a flat 100s timeout per `requests.get()`.
  **Solution:** Share one `requests.Session()` (with `HTTPAdapter`/`Retry` for transient 5xx/connection errors) across the run; lower the default timeout (~20-30s) with per-site override via CSV only where genuinely needed.
  **Benefit:** Fewer transient failures, faster runs.
  **Downside:** Session reuse changes cookie/header state across requests — check no site relies on fully independent per-request sessions.
  **Effort:** S
  **Done 2026-07-04** — added a shared `requests.Session` with 3x retry/backoff on 5xx in both `scraper_standalone.py` and `address_sniffer.py`; timeout set to 30s (was 100s, or entirely unbounded for the Nominatim call in `get_postcode` — that was a latent hang risk, fixed as part of this same change).

- [x] **Problem:** Dead/duplicate code inflates maintenance surface: `scraper.py` (near-identical, superseded copy of `scraper_standalone.py`), `local_event_tracker/` (orphaned 2022 prototype, last git commit 2022-11-11, zero references from any root file, includes a hardcoded personal file path in a Selenium script), `API_request_check.py` (disposable one-off, never wired into the CSV pipeline).
  **Solution:** Delete `scraper.py` and `API_request_check.py`. Delete (or archive on a separate branch/tag) `local_event_tracker/` — git history preserves it if ever needed.
  **Done 2026-07-04** — all three removed via `git rm`; recoverable from git history if ever needed.
  **Benefit:** Removes "which scraper is actually live" confusion, shrinks the repo, removes a leaked personal path.
  **Downside:** None functionally — confirm nothing on PythonAnywhere references these paths before deleting.
  **Effort:** S

---

## 2. Date Parsing

- [x] **Problem:** `date_muncher.munch_munch()` is a hand-rolled ~110-line tokenizer built on `calendar` + regex splitting. It cannot handle any of the CLAUDE.md-named patterns ("second Friday of every month," "Wednesdays - fortnightly," "tours run weekly/monthly," "term time only") — when it finds no day+month tokens it just logs a warning and returns a placeholder. `error.log` confirms this failing today for "Tours run weekly" / "Tours run monthly." `python-dateutil` is already a listed dependency but unused for parsing.
  **Solution:** Layer, don't rewrite: (1) keep `munch_munch` as the fast path for its already-working explicit-date cases; (2) when it returns "no date found," pass the raw string through `dateutil.parser.parse(fuzzy=True)` as a second-pass fallback; (3) for genuinely recurring/relative phrases with no fixed date, explicitly classify them (see next item) rather than forcing a parse. Only reach for `dateparser` if `dateutil` proves insufficient in practice.
  **Benefit:** Fixes real, currently-failing cases; avoids silently mislabeling recurring events as "date not found."
  **Downside:** `fuzzy=True` parsing can misfire on ambiguous text — needs a sanity-range check on the result (ties into §5 validation).
  **Effort:** M
  **Done 2026-07-05** — added `dateutil_fallback()` (guarded with a plausible-year sanity check, `dayfirst=True` for UK conventions) as a second pass when the tokenizer finds no day/month tokens. Verified it recovers oddly-formatted real dates (`15/03/2026`, `March 15 2026`) while genuine garbage strings still correctly fall through to "No date found."

- [x] **Problem:** Recurring-event phrases are indistinguishable from "parsing failed" today.
  **Solution:** Add a small keyword/regex classifier (weekly/monthly/fortnightly/term time/"every <weekday>") that runs before the tokenizer; on match, short-circuit to a `recurring` status that preserves the original phrase for display and is tracked as its own bucket in the run summary.
  **Benefit:** Turns unactionable failures into correctly labeled data; feeds the run-summary metrics CLAUDE.md's scheduling section asks for.
  **Downside:** Regex-based classification will always be incomplete; expect iteration as new phrasings surface.
  **Effort:** S-M
  **Done 2026-07-05** — added `is_recurring_phrase()`, checked before the tokenizer runs. Verified against all 8 CLAUDE.md-listed patterns, including "Available Wednesday to Friday" (weekday-range-with-no-digits, to avoid misfiring on real dated ranges like "Monday 15 to Friday 19 March"). `sort_date`/`end_date` use a `'recurring'` sentinel (parallels the existing `'date not found'`); `month` uses the human-readable `'Recurring'` so the site gets one clean grouped section instead of a raw sentinel string as a heading. Updated `scraper_standalone.event_post_processing`'s dedup mask and duplicate-date-range logic to treat `'recurring'` the same as `'date not found'` — this also surfaced and fixed a latent crash: `datetime.strptime()` on a non-date sentinel value would have raised if it was ever picked up as a group's "max date" (pre-existing risk with `'date not found'` too, now guarded for both).

---

## 3. Location Recognition

- [x] **Problem:** `address_sniffer.sniff_sniff()` does an exact-string match against `addresses_db.csv`, reloading the whole CSV from disk on every call. Whitespace/case/punctuation differences cause avoidable misses that trigger live network calls.
  **Solution:** Load the CSV once per run into memory; normalize keys (strip/lower/collapse whitespace) before lookup; add `rapidfuzz` as a fuzzy-match fallback before falling through to network lookups.
  **Benefit:** Fewer unnecessary network calls, fewer near-duplicate DB rows.
  **Downside:** Fuzzy match needs a conservative similarity threshold to avoid merging two distinct venues with similar names.
  **Effort:** M
  **Done 2026-07-05** — `addresses_db.csv` now loads once per run into a module-level cache with a normalized lookup key, plus a `rapidfuzz.process.extractOne` fallback (`WRatio`, cutoff 93). Verified exact/case/whitespace matches all hit the cache with no network call, and that the fuzzy path catches realistic longer-name typos (e.g. "musuem"→"museum", score ~96) while correctly declining short 2-3 letter differences (e.g. "MTE" vs "MET", score ~86, below the cutoff) — the safer failure mode, since short-string fuzzy matching is more prone to accidentally merging distinct venues.

- [x] **Problem:** Nominatim is called with no rate limiting and no compliant identifying `User-Agent` (violates its usage policy — IP-ban risk). The DuckDuckGo HTML-scrape fallback is fragile and likely already broken.
  **Solution:** Add a descriptive `User-Agent` + a ~1 req/sec throttle for Nominatim. Drop the DuckDuckGo fallback entirely; on geocoding failure, just log "location unresolved."
  **Benefit:** Removes IP-ban risk and a likely-dead code path; simplifies the failure model.
  **Downside:** Slightly lower address-resolution rate for edge cases.
  **Effort:** S
  **Done 2026-07-05** — User-Agent set to `local-event-curator/1.0 (+https://github.com/s-bramer/local_event_curator)` (used the GitHub URL rather than a personal email, to identify the project per Nominatim's policy without putting a personal address in source control — flag if you'd prefer something else). Added a simple `time.monotonic()`-based 1 req/sec throttle before every Nominatim call. DuckDuckGo fallback removed entirely; `get_postcode` now just logs "location unresolved" and returns the existing error sentinel.

- [x] **Problem:** `checkmypostcode.uk` scraping for council/town uses brittle CSS-class matching, caught only by a bare `except:`.
  **Solution:** Leave the approach as-is but narrow the exception handling and log distinctly when the expected selector is simply missing (site changed) vs. a network failure.
  **Effort:** S
  **Done 2026-07-04** — actually completed as part of the §1 reliability pass (the except-narrowing work touched `get_council`/`get_town` directly); not cross-referenced here until now.

- [x] **Problem:** New address lookups are appended to `addresses_db.csv` via plain `to_csv` on every miss, with no locking — a latent corruption risk.
  **Solution:** Write via temp-file-then-atomic-rename, reusing the same pattern being built for the scheduled-run safe publish (§6).
  **Effort:** S
  **Done 2026-07-05** — new entries write to `addresses_db.csv.tmp` then `os.replace()` into place; in-memory cache is refreshed at the same time. Verified in an isolated temp copy: row count increases correctly, the entry is immediately findable, no `.tmp` file is left behind, and the write survives a fresh reload from disk.

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
  **Note (2026-07-05):** PythonAnywhere confirmed as the sole deployment target (Heroku Procfile removed — see §7). One caveat for this item: only 1 of 20 sites (`Visit the Vale`) uses `JSRender` (Playwright). PythonAnywhere has no root/sudo access, and headless Chromium needs system libraries that require it — Playwright is a known pain point there even on paid plans. Thanks to §1's per-site error isolation, a Playwright failure on PythonAnywhere would just log that one site and continue with the other 19 (graceful degradation), but it likely won't update automatically until this is tested or worked around. Worth a dedicated spike before relying on it.

- [x] **Problem:** `error.log` is tracked in git, adding noise on every run.
  **Solution:** Add it (and any per-run logs) to `.gitignore`; untrack the currently-committed copy.
  **Effort:** S
  **Done 2026-07-04** — untracked and gitignored (file itself still exists on disk, still being written to).

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

- [x] **Problem:** `Procfile` (`web: gunicorn main:app`) is a Heroku-style artifact that conflicts with CLAUDE.md's stated PythonAnywhere hosting.
  **Solution:** Confirm whether a Heroku deployment still exists; if not, delete it.
  **Effort:** S
  **Done 2026-07-05** — confirmed PythonAnywhere is the sole target; `Procfile` and its `gunicorn` dependency removed.

---

## 8. Modernization & Dependency Cleanup

- [ ] **Problem:** No type hints on most functions, no dataclasses, no `pathlib`, zero tests — and the two riskiest, bug-prone modules (`date_muncher`, `address_sniffer`) have no safety net for the refactors above.
  **Solution:** Add an `Event` dataclass at the point rows are assembled for output; add type hints opportunistically as functions are touched; add `pytest` coverage for `date_muncher.munch_munch` (explicit cases for every CLAUDE.md-listed date pattern) and `address_sniffer` (mocked network calls) **before** touching their internals in §1-§3.
  **Benefit:** Locks in current (fixed) behavior before refactoring.
  **Effort:** M initial, S ongoing

- [x] **Problem:** `requirements.txt` pins 2022-era versions and is **missing `playwright`, `lxml`, `html5lib` entirely** — a clean install fails today.
  **Solution:** Regenerate from the actual working environment (`pip freeze`), add the three missing packages, bump versions to current stable minors (checked against PythonAnywhere's supported Python version). Drop Windows-only entries (`win-inet-pton`, `PySocks`).
  **Downside:** Version bumps carry a small regression risk — re-run the full scraper across all `events_mode` types after upgrading.
  **Effort:** S-M
  **Done 2026-07-05** — rewrote to list only direct dependencies (pip resolves the rest) at current stable versions (checked live against PyPI, not guessed): Flask 3.1.3, Flask-Mail 0.10.0, beautifulsoup4 4.15.0, lxml 6.1.1, html5lib 1.1, requests 2.34.2, urllib3 2.7.0, pandas 2.3.3, python-dateutil 2.9.0.post0. `playwright` pinned to 1.55.0 (the version already verified working locally) rather than the latest, since browser binaries are version-locked. Dropped `gunicorn` (Heroku-only, see §7), `Flask-Bootstrap` and `python-dotenv` (both unused — confirmed via grep), and Windows-only packages. Verified by creating a fresh `.venv`, installing from the new file, importing every project module, and launching Playwright's Chromium in a smoke test — full scraper run across all `events_mode` types (the noted downside) not yet done, still worth doing before the next production scrape.

- [x] **Problem:** Repo clutter: `.~lock.event_pages.csv#`, `__pycache__/`, `error.log`, and a stale backup CSV (`event_pages_full_list_backup.csv`) committed alongside the live config.
  **Solution:** Add lock files/`__pycache__`/`*.pyc`/`error.log` to `.gitignore`; confirm which backup CSVs are still needed before moving/deleting.
  **Effort:** S
  **Done 2026-07-04** — added `.gitignore`; untracked `__pycache__/` and `error.log` (kept on disk, just no longer versioned); deleted `event_pages_full_list_backup.csv` after diffing it against the live `event_pages.csv` (only difference was one stale URL, confirmed superseded). `event_pages_doc.csv` was **kept** — it's genuine column documentation, not a backup, despite the similar naming.

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

### 2026-07-05 — §2 date parsing and §3 location recognition fixed
Implemented every actionable item in both sections. Date parsing: `date_muncher` now classifies recurring/relative phrases (weekly, fortnightly, "second Friday of...", weekday ranges with no digits, etc.) before attempting a fixed-date parse, and falls back to `dateutil.parser(fuzzy=True)` (year-sanity-checked) for genuinely oddly-formatted real dates the hand-rolled tokenizer can't handle. Location: `address_sniffer` now caches `addresses_db.csv` in memory with normalized-key + `rapidfuzz` matching instead of re-reading the CSV and doing an exact string match on every single lookup; Nominatim calls are throttled to 1/sec with a policy-compliant User-Agent; the DuckDuckGo scrape fallback (already suspected broken) is gone; new address entries write atomically.

Added `rapidfuzz` to `requirements.txt` (installed and verified in `.venv`). Along the way, fixed a `pandas` `FutureWarning` (`transform(max)` → `transform('max')`) and a latent crash risk in `event_post_processing` where a non-date sentinel value picked up as a group's "max date" would blow up `datetime.strptime` — pre-existing for `'date not found'`, now guarded for both sentinels since introducing `'recurring'` doubled the exposure.

Verified with: the exact 8 date patterns named in CLAUDE.md, dateutil-fallback recovery on numeric/reordered dates, confirmation genuine garbage still falls through correctly, a synthetic `event_post_processing` run mixing real/recurring/not-found rows (no crash), and an isolated-temp-copy test of the atomic address-DB write (row count, findability, no leftover `.tmp`, survives a fresh reload).

Not yet done: a real end-to-end scrape against live sites exercising these paths (all verification so far is via direct unit-level calls, not a full `scraper_standalone.py` run) — still recommended before the next production update, same outstanding item as noted in the entry below.

### 2026-07-05 — PythonAnywhere confirmed; requirements.txt refreshed
Confirmed PythonAnywhere as the sole deployment target, so deleted the Heroku `Procfile` (§7, done). Rewrote `requirements.txt` (§8, done) to list only genuine direct dependencies at current stable versions instead of a stale 2022 `pip freeze` dump missing `playwright`/`lxml`/`html5lib`. Verified by creating a fresh `.venv`, doing a clean `pip install -r requirements.txt`, importing every project module (`date_muncher`, `address_sniffer`, `scraper_standalone`, `main`), and smoke-testing a Playwright/Chromium launch — all passed.

Flagged one real risk while confirming PythonAnywhere: only 1 of 20 configured sites (`Visit the Vale`) uses Playwright (`JSRender` mode), and PythonAnywhere's lack of root access makes headless Chromium unreliable there even on paid plans (see the note under §6). Not fixed this session — needs a dedicated spike (test on an actual PythonAnywhere account, or consider running just that one site's scrape elsewhere) before the automated daily run (§6) can be trusted end-to-end.

Not yet done: an actual full scraper run against the refreshed dependencies (only imports/Chromium launch were smoke-tested, not a real scrape across all 20 sites) — worth doing before the next production run.

### 2026-07-04 — §0 bug fixes, §1 reliability, and repo cleanup applied
Pushed a backup checkpoint of the pre-existing working-tree changes to `origin/master` first, then applied all four §0 bug fixes, all three §1 reliability items, and a repo cleanup pass (removed `scraper.py`, `API_request_check.py`, `local_event_tracker/`, and a stale backup CSV; added `.gitignore`; untracked `__pycache__/` and `error.log`). Verified with `python -m py_compile` on all edited files plus a manual functional check of `date_muncher.munch_munch` against sample date strings (including the exact pattern that triggered the original list-mutation bug) to confirm no regression. Committed and pushed as `e928f7f`.

Two open items surfaced during this pass, not yet resolved:
- `Procfile` (`web: gunicorn main:app`) still conflicts with the stated PythonAnywhere hosting — needs your confirmation before it's touched.
- GitHub's Dependabot flagged 59 vulnerabilities on the branch, tied to `requirements.txt`'s stale, incomplete pins (§8) — not addressed this session since it wasn't in scope, but worth prioritizing soon.

Next up per the roadmap sequencing: §8 test harness for `date_muncher`/`address_sniffer`, then §2 date parsing + §3 location as the next robustness pass.

### 2026-07-04 — Roadmap created
Full audit of the scraper pipeline, date/location parsing, Flask app, and repo structure completed. No code changed yet. Confirmed the overall architecture doesn't need a rewrite; debt is concentrated in specific modules (listed above). Added `ROADMAP.md` as the living log for tracking this work. `CLAUDE.md` updated with an access-scope instruction (repo-only, ask before touching anything outside it).
