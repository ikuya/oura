"""Tests for oura.py"""

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from oura import (
    OuraAPIError,
    OuraClient,
    _date_to_datetime_str,
    _format_json,
    _format_table,
    _n_days_ago_str,
    _today_str,
    _validate_date,
    build_parser,
    main,
)


# --- OuraAPIError ---

class TestOuraAPIError:
    def test_stores_status_code_and_message(self):
        err = OuraAPIError(401, "Unauthorized")
        assert err.status_code == 401
        assert err.message == "Unauthorized"

    def test_none_status_code(self):
        err = OuraAPIError(None, "Network error")
        assert err.status_code is None


# --- Date helpers ---

class TestDateHelpers:
    def test_today_str_format(self):
        result = _today_str()
        assert len(result) == 10
        assert result[4] == "-" and result[7] == "-"

    def test_n_days_ago_str(self):
        import datetime
        expected = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        assert _n_days_ago_str(7) == expected

    def test_date_to_datetime_str_start(self):
        assert _date_to_datetime_str("2026-03-28") == "2026-03-28T00:00:00"

    def test_date_to_datetime_str_end_of_day(self):
        assert _date_to_datetime_str("2026-03-28", end_of_day=True) == "2026-03-28T23:59:59"

    def test_validate_date_valid(self):
        assert _validate_date("2026-03-28") == "2026-03-28"

    def test_validate_date_invalid(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _validate_date("2026-13-01")

    def test_validate_date_wrong_format(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _validate_date("28-03-2026")


# --- Formatters ---

class TestFormatJson:
    def test_basic(self):
        records = [{"day": "2026-03-28", "score": 85}]
        result = _format_json(records)
        parsed = json.loads(result)
        assert parsed == records

    def test_empty(self):
        result = _format_json([])
        assert json.loads(result) == []


class TestFormatTable:
    def test_empty_returns_no_data(self):
        assert _format_table([]) == "(no data)"

    def test_single_record(self):
        records = [{"day": "2026-03-28", "score": 85}]
        result = _format_table(records)
        assert "day" in result
        assert "score" in result
        assert "2026-03-28" in result
        assert "85" in result

    def test_header_separator_present(self):
        records = [{"a": "1", "b": "2"}]
        lines = _format_table(records).splitlines()
        # header, separator, data row
        assert len(lines) == 3
        assert set(lines[1].strip()) <= set("- ")

    def test_multiple_records(self):
        records = [
            {"day": "2026-03-27", "score": 80},
            {"day": "2026-03-28", "score": 90},
        ]
        result = _format_table(records)
        assert "2026-03-27" in result
        assert "2026-03-28" in result

    def test_column_width_fits_longest_value(self):
        records = [{"name": "short"}, {"name": "a-very-long-value"}]
        result = _format_table(records)
        assert "a-very-long-value" in result


# --- OuraClient ---

def _make_response(data: list, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"data": data}
    resp.raise_for_status = MagicMock()
    return resp


class TestOuraClient:
    def setup_method(self):
        self.client = OuraClient("test-token")

    def test_auth_header_set(self):
        assert self.client.session.headers["Authorization"] == "Bearer test-token"

    def test_get_daily_sleep(self, mocker):
        expected = [{"day": "2026-03-28", "score": 85}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_sleep("2026-03-21", "2026-03-28")
        assert result == expected
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"
        assert kwargs["params"]["end_date"] == "2026-03-28"

    def test_get_daily_readiness(self, mocker):
        expected = [{"day": "2026-03-28", "score": 70}]
        mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_readiness("2026-03-21", "2026-03-28")
        assert result == expected

    def test_get_heartrate_uses_datetime_params(self, mocker):
        expected = [{"bpm": 60, "timestamp": "2026-03-28T08:00:00"}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        self.client.get_heartrate("2026-03-28", "2026-03-28")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_datetime"] == "2026-03-28T00:00:00"
        assert kwargs["params"]["end_datetime"] == "2026-03-28T23:59:59"

    def test_get_temperature_extracts_fields(self, mocker):
        readiness_data = [
            {
                "day": "2026-03-28",
                "score": 75,
                "temperature_deviation": -0.12,
                "temperature_trend_deviation": -0.05,
                "contributors": {"body_temperature": 95, "hrv_balance": 80},
            }
        ]
        mocker.patch.object(
            self.client.session, "get", return_value=_make_response(readiness_data)
        )
        result = self.client.get_temperature("2026-03-28", "2026-03-28")
        assert result == [
            {
                "day": "2026-03-28",
                "temperature_deviation": -0.12,
                "temperature_trend_deviation": -0.05,
                "body_temperature_score": 95,
            }
        ]

    def test_get_temperature_missing_fields(self, mocker):
        readiness_data = [{"day": "2026-03-28"}]
        mocker.patch.object(
            self.client.session, "get", return_value=_make_response(readiness_data)
        )
        result = self.client.get_temperature("2026-03-28", "2026-03-28")
        assert result[0]["temperature_deviation"] is None
        assert result[0]["body_temperature_score"] is None

    def test_http_error_raises_oura_api_error(self, mocker):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "Internal Server Error"
        http_err = requests.exceptions.HTTPError(response=resp)
        resp.raise_for_status.side_effect = http_err
        mocker.patch.object(self.client.session, "get", return_value=resp)
        with pytest.raises(OuraAPIError) as exc_info:
            self.client.get_daily_sleep("2026-03-21", "2026-03-28")
        assert exc_info.value.status_code == 500

    def test_401_error_includes_hint(self, mocker):
        resp = MagicMock()
        resp.status_code = 401
        resp.text = "Unauthorized"
        http_err = requests.exceptions.HTTPError(response=resp)
        resp.raise_for_status.side_effect = http_err
        mocker.patch.object(self.client.session, "get", return_value=resp)
        with pytest.raises(OuraAPIError) as exc_info:
            self.client.get_daily_sleep("2026-03-21", "2026-03-28")
        assert "OURA_TOKEN" in exc_info.value.message

    def test_network_error_raises_oura_api_error(self, mocker):
        mocker.patch.object(
            self.client.session,
            "get",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        )
        with pytest.raises(OuraAPIError) as exc_info:
            self.client.get_daily_sleep("2026-03-21", "2026-03-28")
        assert exc_info.value.status_code is None

    def test_get_daily_activity(self, mocker):
        expected = [{"day": "2026-03-28", "active_calories": 500}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_activity("2026-03-21", "2026-03-28")
        assert result == expected
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"
        assert kwargs["params"]["end_date"] == "2026-03-28"

    def test_get_daily_stress(self, mocker):
        expected = [{"day": "2026-03-28", "stress_high": 120}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_stress("2026-03-21", "2026-03-28")
        assert result == expected
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"

    def test_get_daily_spo2(self, mocker):
        expected = [{"day": "2026-03-28", "spo2_percentage": {"average": 97.5}}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_spo2("2026-03-21", "2026-03-28")
        assert result == expected
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"

    def test_get_daily_resilience(self, mocker):
        expected = [{"day": "2026-03-28", "level": "solid"}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_resilience("2026-03-21", "2026-03-28")
        assert result == expected
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"

    def test_get_daily_cardiovascular_age(self, mocker):
        expected = [{"day": "2026-03-28", "vascular_age": 35}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_daily_cardiovascular_age("2026-03-21", "2026-03-28")
        assert result == expected
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"

    def test_get_vo2_max(self, mocker):
        expected = [{"day": "2026-03-28", "vo2_max": 52.0}]
        mock_get = mocker.patch.object(
            self.client.session, "get", return_value=_make_response(expected)
        )
        result = self.client.get_vo2_max("2026-03-21", "2026-03-28")
        assert result == expected
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["start_date"] == "2026-03-21"


# --- CLI (build_parser / main) ---

class TestBuildParser:
    def test_sleep_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["--token", "tok", "sleep"])
        assert args.command == "sleep"
        assert args.token == "tok"

    def test_default_format_is_table(self):
        parser = build_parser()
        args = parser.parse_args(["--token", "tok", "sleep"])
        assert args.format == "table"

    def test_format_json(self):
        parser = build_parser()
        args = parser.parse_args(["--token", "tok", "sleep", "--format", "json"])
        assert args.format == "json"

    def test_invalid_date_raises(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--token", "tok", "sleep", "--start", "bad-date"])

    def test_all_subcommands_exist(self):
        parser = build_parser()
        for cmd in ["sleep", "readiness", "heartrate", "temperature", "all"]:
            args = parser.parse_args(["--token", "tok", cmd])
            assert args.command == cmd


class TestMain:
    def _run(self, argv, mock_client):
        with patch("sys.argv", ["oura"] + argv):
            with patch("oura.OuraClient", return_value=mock_client):
                main()

    def _make_client(self, data=None):
        client = MagicMock()
        records = data or [{"day": "2026-03-28", "score": 85}]
        client.get_daily_sleep.return_value = records
        client.get_daily_readiness.return_value = records
        client.get_heartrate.return_value = records
        client.get_temperature.return_value = records
        client.get_daily_activity.return_value = records
        client.get_daily_stress.return_value = records
        client.get_daily_spo2.return_value = records
        client.get_daily_resilience.return_value = records
        client.get_daily_cardiovascular_age.return_value = records
        client.get_vo2_max.return_value = records
        return client

    def test_sleep_command(self, capsys):
        client = self._make_client()
        self._run(["--token", "tok", "sleep"], client)
        client.get_daily_sleep.assert_called_once()

    def test_readiness_command(self, capsys):
        client = self._make_client()
        self._run(["--token", "tok", "readiness"], client)
        client.get_daily_readiness.assert_called_once()

    def test_heartrate_command(self, capsys):
        client = self._make_client()
        self._run(["--token", "tok", "heartrate"], client)
        client.get_heartrate.assert_called_once()

    def test_temperature_command(self, capsys):
        client = self._make_client()
        self._run(["--token", "tok", "temperature"], client)
        client.get_temperature.assert_called_once()

    def test_all_command_calls_all_fetchers(self, capsys):
        client = self._make_client()
        self._run(["--token", "tok", "all"], client)
        client.get_daily_sleep.assert_called_once()
        client.get_daily_readiness.assert_called_once()
        client.get_heartrate.assert_called_once()
        client.get_temperature.assert_called_once()
        client.get_daily_activity.assert_called_once()
        client.get_daily_stress.assert_called_once()
        client.get_daily_spo2.assert_called_once()
        client.get_daily_resilience.assert_called_once()
        client.get_daily_cardiovascular_age.assert_called_once()
        client.get_vo2_max.assert_called_once()

    def test_all_command_json_output(self, capsys):
        records = [{"day": "2026-03-28", "score": 85}]
        client = self._make_client(records)
        self._run(["--token", "tok", "all", "--format", "json"], client)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert set(parsed.keys()) == {
            "sleep", "readiness", "heartrate", "temperature",
            "activity", "stress", "spo2", "resilience",
            "cardiovascular_age", "vo2_max",
        }
        assert parsed["sleep"] == records

    def test_json_format_output(self, capsys):
        client = self._make_client([{"day": "2026-03-28", "score": 85}])
        self._run(["--token", "tok", "sleep", "--format", "json"], client)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed[0]["score"] == 85

    def test_no_token_exits(self):
        with patch("sys.argv", ["oura", "sleep"]):
            with patch.dict("os.environ", {}, clear=True):
                with patch("oura.load_dotenv"):
                    with pytest.raises(SystemExit):
                        main()

    def test_api_error_exits_with_code_1(self):
        client = MagicMock()
        client.get_daily_sleep.side_effect = OuraAPIError(500, "Server error")
        with pytest.raises(SystemExit) as exc_info:
            self._run(["--token", "tok", "sleep"], client)
        assert exc_info.value.code == 1

    def test_api_error_json_format_outputs_json(self, capsys):
        client = MagicMock()
        client.get_daily_sleep.side_effect = OuraAPIError(404, "HTTP 404: Not Found")
        with pytest.raises(SystemExit):
            self._run(["--token", "tok", "sleep", "--format", "json"], client)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["status_code"] == 404
        assert "error" in parsed

    def test_api_error_table_format_outputs_to_stderr(self, capsys):
        client = MagicMock()
        client.get_daily_sleep.side_effect = OuraAPIError(404, "HTTP 404: Not Found")
        with pytest.raises(SystemExit):
            self._run(["--token", "tok", "sleep"], client)
        out, err = capsys.readouterr()
        assert out == ""
        assert "Error:" in err
