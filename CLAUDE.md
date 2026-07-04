## Project Overview

This project is a Python-based local event aggregation system that scrapes event listings from multiple local event websites, normalises the data, stores the results in CSV files, and serves them through a Flask web application hosted on PythonAnywhere.

The project was originally written several years ago and is functional, but has accumulated technical debt. The objective is to modernise, improve robustness, reduce maintenance effort, and make the scraper resilient to changes in source websites.

The scraper should eventually run automatically, ideally once per day, to keep the Flask website updated without manual intervention.

The project is not intended to become a large distributed system or use unnecessary frameworks. Simplicity and maintainability are priorities.

---

# Overall Objectives

When making changes, prioritise:

1. Correctness
2. Robustness
3. Maintainability
4. Readability
5. Minimal unnecessary complexity

Avoid rewriting working code purely for style reasons.

Prefer incremental improvements over complete rewrites.

---

# Existing Architecture

The scraper currently:

* Reads configuration from CSV files.
* Each CSV entry describes:

  * event website
  * selectors/tags
  * extraction methods
  * event URL
  * title extraction
  * date extraction
  * location extraction
  * other required metadata
* Uses primarily BeautifulSoup for parsing.
* Produces a consolidated CSV of events.
* Flask reads this CSV and displays events via a website.
* Hosted on PythonAnywhere.

The scraper is intentionally data-driven via CSV configuration rather than having hardcoded logic for each site.

---

# Known Problems

The current system has a number of weaknesses.

## Date Parsing

Dates are currently fragile.

Examples include:

* inconsistent formats
* "Wednesdays - fortnightly"
* "Second Friday of every month"
* "Last Friday of each month"
* "Tours run weekly"
* "Tours run monthly"
* "Multiple dates available"
* "Term time only"
* "Available Wednesday to Friday"

Investigate replacing custom parsing with a more robust solution where appropriate.

---

## Location Recognition

Location extraction is unreliable.

Problems include:

* inconsistent address format
* tool needs to recognise address, find location/town
* currently using a address csv to handle common addresses othewise tries to find it

Investigate:

* better parsing
* optional geocoding
* venue normalisation
* configurable extraction rules

---

## Dynamic Websites

Several websites have become JavaScript-driven.

Examples include failures on Eventbrite and other modern event platforms.

Implement a progressive strategy:

requests + BeautifulSoup
inspect embedded JSON
Playwright (only if required)

Avoid using Playwright unless earlier stages fail.

The scraper should automatically choose the lightest successful approach.

---

## HTML Changes

Minor HTML changes frequently break scrapers.

Improve resilience by:

* fallback selectors
* validation
* graceful failures
* informative logging
* configurable extraction strategies

---

## Error Handling

Current error handling needs review.

Improve:

* exception handling
* logging
* retry behaviour
* timeout handling
* user-agent management
* network failures

The scraper should continue processing other sites if one fails.

---

## Data Validation

Validate scraped events before inclusion.

Examples:

* missing title
* invalid date
* malformed URLs
* duplicate events
* blank records

---

## Duplicate Detection

Review duplicate detection.

Potential improvements:

* URL matching
* fuzzy title matching
* date + venue comparison

Avoid obvious duplicate listings.

---

## Configuration

Review the CSV configuration format.

Possible improvements:

* validation
* clearer field names
* documentation
* defaults
* optional fields

Do not unnecessarily replace CSV with another format unless there is a compelling reason.

---

# Code Modernisation

Update the project to current Python best practices.

Potential improvements include:

* type hints
* dataclasses where appropriate
* pathlib
* logging module
* modern exception handling
* f-strings
* improved project structure
* dependency management
* removal of obsolete code

Only introduce modern language features when they improve readability.

---

# Performance

Review for performance improvements.

Potential areas:

* HTTP session reuse
* concurrent downloads where appropriate
* caching
* reducing duplicate requests

Do not optimise prematurely.

Maintain readability.

---

# Flask Application

Review the Flask application for:

* structure
* routing
* template organisation
* filtering
* sorting
* pagination
* error handling

Keep the application lightweight.

---

# PythonAnywhere

The application is hosted on PythonAnywhere.

Changes should remain compatible with that environment unless there is a strong justification otherwise.

---

# Testing

Where practical:

* add unit tests
* add parsing tests
* create sample HTML fixtures
* make scraper behaviour testable without hitting live websites

Tests are preferable to manual verification.

---

# Documentation

Improve documentation where needed.

Document:

* project structure
* scraper workflow
* configuration format
* adding new websites
* deployment process

---

# Refactoring Principles

When refactoring:

* preserve behaviour unless fixing a bug
* make small, reviewable commits
* explain significant architectural decisions
* remove dead code
* avoid unnecessary abstractions

Do not introduce frameworks simply because they are modern.

---

# Suggestions Encouraged

Please identify opportunities for improvement beyond those listed above.

For each significant suggestion, explain:

* the problem
* the proposed solution
* expected benefits
* possible downsides
* implementation effort

---

# Preferred Libraries

Where appropriate, consider:

* BeautifulSoup
* requests
* dateparser
* python-dateutil
* Playwright (only where justified)
* rapidfuzz
* pandas (only if it genuinely simplifies processing)

Avoid introducing heavy dependencies without clear benefit.

---

# Desired Outcome

The end result should be:

* easier to maintain
* more robust to website changes
* better at parsing dates and locations
* tolerant of failures
* easier to extend with new event websites
* well documented
* tested
* compatible with current Python versions

Focus on producing clean, pragmatic engineering rather than a complete redesign.

# Scheduled Automatic Runs

The scraper should eventually run automatically, ideally once per day, to keep the Flask website updated without manual intervention.

## Goal

Implement a reliable scheduled update process that:

* runs the scraper automatically
* updates the consolidated events CSV
* refreshes the website data
* logs each run clearly
* fails safely without breaking the live website

## PythonAnywhere Compatibility

The project is hosted on PythonAnywhere, so scheduling should be designed around PythonAnywhere scheduled tasks unless there is a strong reason to use another approach.

Assume the daily run may be triggered by a command such as:

```bash
python run_scraper.py
```

or similar.

## Requirements

The scheduled scraper should:

* run unattended
* use production-safe paths
* avoid interactive prompts
* write logs to a predictable location
* preserve the previous valid events CSV if the new scrape fails
* avoid publishing obviously broken or empty output
* produce a run summary
* make failures easy to diagnose

## Safe Publishing Workflow

Do not overwrite the live events CSV directly.

Prefer a staged workflow:

```text
scrape events
write temporary output CSV
validate output
compare with previous output
if valid, replace live CSV atomically
if invalid, keep previous live CSV
write run summary
```

## Validation Before Publishing

Before replacing the live CSV, check:

* output file exists
* output is not empty
* expected columns are present
* number of events is within a reasonable range
* dates are parseable or explicitly marked as unknown/recurring
* required fields are present where possible
* duplicate rate is not suspiciously high

## Logging and Monitoring

Each scheduled run should produce a clear summary, including:

```text
Run started
Run completed
Sites processed
Sites failed
Events scraped
Events published
Events discarded
Date parsing failures
Location failures
Title failures
Network failures
Output CSV path
Previous CSV preserved or replaced
```

## Failure Handling

If a scrape partially fails, the system should still publish valid results if the output passes validation.

If the scrape fails badly, the website should continue using the previous known-good CSV.

The scheduled job should never leave the website with a missing, empty, or corrupt events file.

## Future Enhancements

Consider adding:

* email notification on failed runs
* summary email after each daily run
* simple admin/status page showing last successful scrape
* timestamp of last update on the Flask site
* archived CSV snapshots
* per-site failure history
* retry failed sites only

Never modify files outside this repository. Assume this repository is the complete project unless I explicitly tell you otherwise. If you believe a file outside the repository is needed, ask first.
