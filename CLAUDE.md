# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run oura.py <subcommand> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--format {json,table}]

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_oura.py::TestOuraClient::test_get_sleep -v
```

## Architecture

Single-file application (`oura.py`) wrapping the Oura Ring API v2. The code is organized into these layers:

1. **`OuraClient`** — `requests.Session`-based HTTP client. Each public method maps to one API endpoint. The private `_get()` method centralizes auth, error handling, and JSON parsing.
2. **Output formatters** — `_format_json` and `_format_table` convert raw API data into human-readable output. Dispatch via `_print_output()`.
3. **CLI (`build_parser` / `main`)** — `argparse`-based. Five subcommands: `sleep`, `readiness`, `heartrate`, `temperature`, `all`. Common args (`--start`, `--end`, `--format`, `--token`) are added via `_add_common_args()`.

`temperature` data is derived from the readiness endpoint, not a dedicated endpoint.

## Authentication

Token is read from `$OURA_TOKEN` env var (loaded via `.env`) or `--token` flag. A 401 response triggers a user-friendly error message pointing to the token setup.

## Testing

Tests use `pytest-mock` to mock HTTP responses — no real API calls are made. The test file mirrors the structure of `oura.py` with one test class per module section.
