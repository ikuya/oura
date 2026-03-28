#!/usr/bin/env python3
"""Oura Ring API v2 wrapper CLI."""

import argparse
import datetime
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.ouraring.com"
API_TIMEOUT = 15
DATE_FORMAT = "%Y-%m-%d"


class OuraAPIError(Exception):
    def __init__(self, status_code: int | None, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class OuraClient:
    def __init__(self, token: str) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get(self, path: str, params: dict) -> list[dict]:
        url = BASE_URL + path
        try:
            response = self.session.get(url, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            msg = f"HTTP {status}: {e.response.text if e.response is not None else str(e)}"
            if status == 401:
                msg += "\nHint: Check your OURA_TOKEN."
            raise OuraAPIError(status, msg) from e
        except requests.exceptions.RequestException as e:
            raise OuraAPIError(None, f"Request failed: {e}") from e
        return response.json().get("data", [])

    def get_daily_sleep(self, start: str, end: str) -> list[dict]:
        return self._get(
            "/v2/usercollection/daily_sleep",
            {"start_date": start, "end_date": end},
        )

    def get_daily_readiness(self, start: str, end: str) -> list[dict]:
        return self._get(
            "/v2/usercollection/daily_readiness",
            {"start_date": start, "end_date": end},
        )

    def get_heartrate(self, start: str, end: str) -> list[dict]:
        return self._get(
            "/v2/usercollection/heartrate",
            {
                "start_datetime": _date_to_datetime_str(start),
                "end_datetime": _date_to_datetime_str(end, end_of_day=True),
            },
        )

    def get_temperature(self, start: str, end: str) -> list[dict]:
        records = self.get_daily_readiness(start, end)
        return [
            {
                "day": r.get("day"),
                "temperature_deviation": r.get("temperature_deviation"),
                "temperature_trend_deviation": r.get("temperature_trend_deviation"),
                "body_temperature_score": r.get("contributors", {}).get("body_temperature"),
            }
            for r in records
        ]


# --- Date helpers ---

def _today_str() -> str:
    return datetime.date.today().strftime(DATE_FORMAT)


def _n_days_ago_str(n: int) -> str:
    return (datetime.date.today() - datetime.timedelta(days=n)).strftime(DATE_FORMAT)


def _date_to_datetime_str(date_str: str, end_of_day: bool = False) -> str:
    time = "23:59:59" if end_of_day else "00:00:00"
    return f"{date_str}T{time}"


def _validate_date(value: str) -> str:
    try:
        datetime.datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: '{value}'. Expected YYYY-MM-DD.")
    return value


# --- Formatters ---

def _format_json(records: list[dict]) -> str:
    return json.dumps(records, ensure_ascii=False, indent=2)


def _format_table(records: list[dict]) -> str:
    if not records:
        return "(no data)"
    headers = list(records[0].keys())
    rows = [[str(r.get(h, "")) for h in headers] for r in records]
    widths = [
        max(len(h), max((len(row[i]) for row in rows), default=0))
        for i, h in enumerate(headers)
    ]
    sep = "  ".join("-" * w for w in widths)
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    data_lines = [
        "  ".join(cell.ljust(w) for cell, w in zip(row, widths)) for row in rows
    ]
    return "\n".join([header_line, sep] + data_lines)


def _print_output(records: list[dict], fmt: str) -> None:
    if fmt == "json":
        print(_format_json(records))
    else:
        print(_format_table(records))


# --- CLI ---

def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--start",
        type=_validate_date,
        default=_n_days_ago_str(7),
        metavar="YYYY-MM-DD",
        help="Start date (default: 7 days ago)",
    )
    parser.add_argument(
        "--end",
        type=_validate_date,
        default=_today_str(),
        metavar="YYYY-MM-DD",
        help="End date (default: today)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Output format (default: table)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oura",
        description="Oura Ring API v2 CLI wrapper",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("OURA_TOKEN"),
        help="Personal access token (default: $OURA_TOKEN)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in [
        ("sleep", "Daily sleep scores and contributors"),
        ("readiness", "Daily readiness scores and contributors"),
        ("heartrate", "Heart rate time series (5-min intervals)"),
        ("temperature", "Body temperature deviation from readiness data"),
        ("all", "All of the above"),
    ]:
        sub = subparsers.add_parser(name, help=help_text)
        _add_common_args(sub)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.token:
        parser.error(
            "No token provided. Set OURA_TOKEN in .env or environment, or use --token."
        )

    client = OuraClient(args.token)

    try:
        if args.command == "sleep":
            _print_output(client.get_daily_sleep(args.start, args.end), args.format)

        elif args.command == "readiness":
            _print_output(client.get_daily_readiness(args.start, args.end), args.format)

        elif args.command == "heartrate":
            _print_output(client.get_heartrate(args.start, args.end), args.format)

        elif args.command == "temperature":
            _print_output(client.get_temperature(args.start, args.end), args.format)

        elif args.command == "all":
            sections = [
                ("Sleep", client.get_daily_sleep),
                ("Readiness", client.get_daily_readiness),
                ("Heart Rate", client.get_heartrate),
                ("Temperature", client.get_temperature),
            ]
            for title, fetch in sections:
                print(f"\n=== {title} ===")
                _print_output(fetch(args.start, args.end), args.format)

    except OuraAPIError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
