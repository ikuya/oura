# Graph Report - oura  (2026-09-04)

## Corpus Check
- Corpus is ~3,088 words - fits in a single context window. You may not need a graph.

## Summary
- 129 nodes · 267 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.93)
- Token cost: 6,000 input · 4,000 output

## Community Hubs (Navigation)
- Date Helpers & JSON Output
- API Client Test Suite
- Error Handling & Main Entrypoint Tests
- CLI Subcommand Surface
- Argument Parser Construction
- Oura API Client Methods
- Table Formatting
- Token Authentication
- Temperature From Readiness
- Oura API Access Requirements

## God Nodes (most connected - your core abstractions)
1. `TestOuraClient` - 21 edges
2. `OuraClient` - 20 edges
3. `TestMain` - 16 edges
4. `build_parser()` - 14 edges
5. `Oura CLI Wrapper` - 14 edges
6. `OuraAPIError` - 13 edges
7. `_make_response()` - 12 edges
8. `all subcommand` - 12 edges
9. `main()` - 11 edges
10. `_format_table()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Oura Ring API v2` --references--> `OuraClient`  [EXTRACTED]
  README_ja.md → oura.py
- `heartrate subcommand` --shares_data_with--> `_date_to_datetime_str()`  [INFERRED]
  README.md → oura.py
- `Table Output Format` --references--> `_print_output()`  [INFERRED]
  README.md → oura.py
- `--date Single-Day Override` --rationale_for--> `main()`  [INFERRED]
  README.md → oura.py
- `Oura CLI ラッパー` --semantically_similar_to--> `Oura CLI Wrapper`  [INFERRED] [semantically similar]
  README_ja.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Biometric Retrieval Surface** — readme_subcommand_sleep, readme_subcommand_readiness, readme_subcommand_heartrate, readme_subcommand_temperature, readme_subcommand_activity, readme_subcommand_stress, readme_subcommand_spo2, readme_subcommand_resilience, readme_subcommand_cardiovascular_age, readme_subcommand_vo2_max, readme_subcommand_scores, readme_subcommand_all [EXTRACTED 1.00]
- **Token Authentication Flow** — readme_personal_access_token, readme_oura_token_env, oura_main, oura_ouraclient_init, oura_ouraapierror [INFERRED 0.85]
- **Temperature Derivation From Readiness** — readme_temperature_derivation, readme_daily_readiness_endpoint, oura_ouraclient_get_temperature, oura_ouraclient_get_daily_readiness, readme_subcommand_temperature [EXTRACTED 1.00]

## Communities (11 total, 2 thin omitted)

### Community 0 - "Date Helpers & JSON Output"
Cohesion: 0.14
Nodes (15): _add_common_args(), _date_to_datetime_str(), _format_json(), _n_days_ago_str(), _print_output(), _today_str(), _validate_date(), --date Single-Day Override (+7 more)

### Community 2 - "Error Handling & Main Entrypoint Tests"
Cohesion: 0.25
Nodes (4): Exception, OuraAPIError, TestMain, TestOuraAPIError

### Community 3 - "CLI Subcommand Surface"
Cohesion: 0.31
Nodes (13): Oura CLI Wrapper, activity subcommand, all subcommand, cardiovascular_age subcommand, heartrate subcommand, readiness subcommand, resilience subcommand, scores subcommand (+5 more)

### Community 4 - "Argument Parser Construction"
Cohesion: 0.26
Nodes (5): ArgumentParser, build_parser(), Oura CLI ラッパー, サブコマンド一覧（日本語）, TestBuildParser

### Community 6 - "Table Formatting"
Cohesion: 0.36
Nodes (4): _format_table(), テーブル出力フォーマット, Table Output Format, TestFormatTable

### Community 7 - "Token Authentication"
Cohesion: 0.29
Nodes (5): main(), OURA_TOKEN 環境変数, Personal Access Token（アクセストークン）, OURA_TOKEN Environment Variable, Personal Access Token

### Community 8 - "Temperature From Readiness"
Cohesion: 0.60
Nodes (4): /v2/usercollection/daily_readiness, /v2/usercollection/daily_readiness, 体温はレディネスから抽出, Temperature Derived From Readiness

### Community 9 - "Oura API Access Requirements"
Cohesion: 0.50
Nodes (4): Oura Membership 要件, Oura Ring API v2, Oura Membership Requirement, Oura Ring API v2

## Knowledge Gaps
- **4 isolated node(s):** `Personal Access Token（アクセストークン）`, `Oura Membership 要件`, `デフォルト7日間の期間`, `--date による単日指定の優先`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OuraClient` connect `Oura API Client Methods` to `Date Helpers & JSON Output`, `API Client Test Suite`, `Token Authentication`, `Temperature From Readiness`, `Oura API Access Requirements`?**
  _High betweenness centrality (0.286) - this node is a cross-community bridge._
- **Why does `TestOuraClient` connect `API Client Test Suite` to `Date Helpers & JSON Output`, `Error Handling & Main Entrypoint Tests`, `Oura API Client Methods`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `main()` connect `Token Authentication` to `Date Helpers & JSON Output`, `Error Handling & Main Entrypoint Tests`, `CLI Subcommand Surface`, `Argument Parser Construction`, `Oura API Client Methods`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `TestOuraClient` (e.g. with `OuraAPIError` and `OuraClient`) actually correct?**
  _`TestOuraClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Personal Access Token（アクセストークン）`, `Oura Membership 要件`, `デフォルト7日間の期間` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Date Helpers & JSON Output` be split into smaller, more focused modules?**
  _Cohesion score 0.14461538461538462 - nodes in this community are weakly interconnected._