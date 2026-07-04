# CLAUDE.md

## Project

This project scrapes local event listings from many websites, normalises the results into a single CSV, and serves them via a lightweight Flask website hosted on PythonAnywhere.

The scraper has evolved over several years and works well overall, but it now requires modernisation and improved resilience.

The objective is to improve the existing system—not rewrite it.

---

# Guiding Principles

* Prefer incremental improvements over large rewrites.
* Preserve existing behaviour unless fixing a bug.
* Keep solutions simple and maintainable.
* Reduce per-site maintenance wherever possible.
* Explain significant architectural changes before implementing them.

---

# Existing Design

The scraper is intentionally configuration-driven.

Most websites are defined by CSV configuration rather than hard-coded Python.

Current pipeline:

1. Read site configuration CSV.
2. Discover event pages.
3. Extract event fields.
4. Parse dates.
5. Parse locations.
6. Post-process and deduplicate.
7. Write consolidated CSV.
8. Flask displays the resulting events.

Preserve this overall architecture unless there is a compelling reason to change it.

---

# Highest Priorities

Focus work in roughly this order.

## 1. Reliability

Improve robustness against:

* HTML changes
* missing fields
* malformed pages
* network failures
* JavaScript-driven sites

The scraper should continue processing remaining sites if one fails.

---

## 2. Date Parsing

The current date parser is fragile.

Support recurring and natural-language dates such as:

* weekly
* fortnightly
* monthly
* second Friday
* last Thursday
* term time
* multiple dates

Prefer generic parsing over increasing numbers of special cases.

---

## 3. Location Recognition

Current postcode-based matching is too limited.

Improve venue recognition by separating:

* venue
* address
* town
* postcode
* coordinates

Recognise known venues even when a postcode is absent.

---

## 4. Extraction Strategy

Use a layered approach:

1. BeautifulSoup
2. embedded JSON / JSON-LD
3. OpenGraph metadata
4. Playwright when genuinely required

Avoid browser automation unless necessary.

---

## 5. Validation

Validate every scraped event before publishing.

Check for:

* title
* date
* location
* URL
* duplicates

Retain useful events even if some fields cannot be extracted.

---

## 6. Logging

Produce useful diagnostics.

Each run should summarise:

* sites processed
* failures
* events scraped
* discarded events
* parsing failures by type

Logging should help identify failing websites quickly.

---

# Refactoring Goals

Modernise the codebase where it provides clear value.

Examples include:

* type hints
* pathlib
* dataclasses where appropriate
* improved project structure
* smaller functions
* clearer naming
* better error handling
* reusable components
* unit tests

Avoid refactoring purely for style.

---

# Scheduled Operation

The scraper should eventually run automatically once per day on PythonAnywhere.

The automated run must:

* execute unattended
* validate output before publishing
* never replace a valid CSV with an empty or corrupt one
* preserve the previous successful output if validation fails
* produce a clear run summary

Publishing should be atomic so the website always serves a valid dataset.

---

# When Improving the Project

Before making major changes:

* identify the root cause
* propose the simplest robust solution
* estimate implementation effort
* explain trade-offs

Prefer removing complexity over adding it.

The goal is a scraper that requires minimal ongoing maintenance while remaining easy to understand and extend.
