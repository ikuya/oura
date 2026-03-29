# oura

A CLI wrapper for the Oura Ring API v2. Retrieves sleep, readiness, heart rate, body temperature, activity, stress, SpO2, resilience, cardiovascular age, and VO2 max data.

## Getting an Access Token

1. Visit https://cloud.ouraring.com/personal-access-tokens (login required)
2. Click **"Create A New Personal Access Token"**
3. Enter a name describing the token's purpose (e.g. `oura-cli`)
4. Click **"Create"**
5. Copy the displayed token (it will not be shown again after closing this page)

> **Note:** API access requires an active Oura Membership. Not available for Gen3 / Oura Ring 4 without a membership.

## Setup

```bash
# Install dependencies
uv sync

# Set the token in .env
echo "OURA_TOKEN=your_token_here" > .env
```

## Usage

```bash
uv run oura.py <subcommand> [options]
```

### Subcommands

| Command | Description |
|---|---|
| `sleep` | Sleep score and contributors |
| `readiness` | Readiness score and contributors |
| `heartrate` | Heart rate time-series data (5-minute intervals) |
| `temperature` | Body temperature deviation (extracted from readiness data) |
| `activity` | Daily activity summary and calorie breakdown |
| `stress` | Daily stress levels |
| `spo2` | Blood oxygen saturation (SpO2) |
| `resilience` | Daily resilience level |
| `cardiovascular_age` | Cardiovascular age estimate |
| `vo2_max` | VO2 max fitness metric |
| `all` | All biometric endpoints (sleep, readiness, heartrate, temperature, activity, stress, spo2, resilience, cardiovascular_age, vo2_max) — table format shows each section separately; `--format json` outputs a single combined JSON object |

### Options

| Option | Default | Description |
|---|---|---|
| `--start YYYY-MM-DD` | 7 days ago | Start date |
| `--end YYYY-MM-DD` | Today | End date |
| `--format {json,table}` | `table` | Output format |
| `--token TOKEN` | `$OURA_TOKEN` | Personal Access Token |

## Examples

```bash
# Sleep data for the last 7 days (table format)
uv run oura.py sleep

# Readiness data for a specific date range in JSON format
uv run oura.py readiness --start 2026-03-01 --end 2026-03-28 --format json

# Heart rate for today
uv run oura.py heartrate --start 2026-03-28 --end 2026-03-28

# Body temperature deviation
uv run oura.py temperature --start 2026-03-01

# Fetch all data at once (table format)
uv run oura.py all --start 2026-03-27 --end 2026-03-28

# Fetch all biometric data as a single JSON object
uv run oura.py all --start 2026-03-27 --end 2026-03-28 --format json
```

## Data Sources

Body temperature data has no dedicated endpoint, so it is extracted from the readiness endpoint (`/v2/usercollection/daily_readiness`) using the following fields:

| Field | Description |
|---|---|
| `temperature_deviation` | Deviation from personal baseline (°C) |
| `temperature_trend_deviation` | Trend deviation (°C) |
| `body_temperature_score` | Contribution of body temperature to readiness score (1–100) |
