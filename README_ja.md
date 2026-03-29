# oura

Oura Ring API v2 の CLI ラッパースクリプト。睡眠・レディネス・心拍数・体温・活動量・ストレス・SpO2・レジリエンス・心血管年齢・VO2 max データを取得できる。

## アクセストークンの取得

1. https://cloud.ouraring.com/personal-access-tokens にアクセス（要ログイン）
2. **"Create A New Personal Access Token"** をクリック
3. トークンの用途を表す名前を入力（例: `oura-cli`）
4. **"Create"** をクリック
5. 表示されたトークンをコピー（この画面を閉じると二度と表示されない）

> **注意:** Oura Membership が有効なアカウントのみ API アクセスが可能。Gen3 / Oura Ring 4 でメンバーシップなしの場合は利用不可。

## セットアップ

```bash
# 依存関係のインストール
uv sync

# 取得したトークンを .env に設定
echo "OURA_TOKEN=your_token_here" > .env
```

## 使い方

```bash
uv run oura.py <subcommand> [options]
```

### サブコマンド

| コマンド | 内容 |
|---|---|
| `sleep` | 睡眠スコアとコントリビューター |
| `readiness` | レディネススコアとコントリビューター |
| `heartrate` | 心拍数の時系列データ（5分間隔） |
| `temperature` | 体温偏差（レディネスデータから抽出） |
| `activity` | 1日の活動量サマリーとカロリー内訳 |
| `stress` | 1日のストレスレベル |
| `spo2` | 血中酸素飽和度（SpO2） |
| `resilience` | 1日のレジリエンスレベル |
| `cardiovascular_age` | 心血管年齢の推定値 |
| `vo2_max` | VO2 max（最大酸素摂取量）フィットネス指標 |
| `all` | 全 Biometric エンドポイント（sleep, readiness, heartrate, temperature, activity, stress, spo2, resilience, cardiovascular_age, vo2_max）— table 形式は各セクションを個別に表示、`--format json` で1つの統合 JSON として出力 |

### オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--start YYYY-MM-DD` | 7日前 | 開始日 |
| `--end YYYY-MM-DD` | 今日 | 終了日 |
| `--date YYYY-MM-DD` | — | 1日分のデータを取得（`--start` / `--end` より優先） |
| `--format {json,table}` | `table` | 出力フォーマット |
| `--token TOKEN` | `$OURA_TOKEN` | Personal Access Token |

## 実行例

```bash
# 直近7日の睡眠データ（テーブル表示）
uv run oura.py sleep

# 期間指定してレディネスを JSON で出力
uv run oura.py readiness --start 2026-03-01 --end 2026-03-28 --format json

# 特定の1日の心拍数
uv run oura.py heartrate --date 2026-03-28

# 体温偏差
uv run oura.py temperature --start 2026-03-01

# すべてのデータをまとめて取得（テーブル表示）
uv run oura.py all --start 2026-03-27 --end 2026-03-28

# すべての Biometric データを1つの JSON で取得
uv run oura.py all --start 2026-03-27 --end 2026-03-28 --format json
```

## データソース

体温データは専用エンドポイントがないため、レディネスエンドポイント（`/v2/usercollection/daily_readiness`）から以下のフィールドを抽出している。

| フィールド | 説明 |
|---|---|
| `temperature_deviation` | 個人ベースラインからの偏差（℃） |
| `temperature_trend_deviation` | トレンド偏差（℃） |
| `body_temperature_score` | 体温のレディネスへの貢献スコア（1–100） |
