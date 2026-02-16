# GA4 Config Checker

GA4（Google Analytics 4）プロパティの設定を自動チェックし、監査レポートを生成するツール。

## チェック項目

| カテゴリ | 内容 |
|---------|------|
| **プロパティ基本設定** | 業種・タイムゾーン・通貨設定、データストリーム、拡張計測機能 |
| **イベント/コンバージョン** | コンバージョン設定状況、推奨イベント、命名規則チェック |
| **カスタム定義** | カスタムディメンション・指標の使用状況、上限チェック、説明文の有無 |
| **データ保持/プライバシー** | データ保持期間、アクティビティリセット設定 |

## セットアップ

```bash
pip install -r requirements.txt
```

### 認証

以下のいずれかの方法で認証：

1. **サービスアカウントキー** を `--credentials` で指定
2. **Application Default Credentials (ADC)** を使用（`gcloud auth application-default login`）

GA4 Admin API の読み取り権限（`analytics.readonly`）が必要です。

## 使い方

```bash
# 基本実行
python -m ga4_checker --property-id 123456789

# サービスアカウント指定
python -m ga4_checker -p 123456789 -c service-account-key.json

# 設定ファイルで実行
python -m ga4_checker --config config.yaml

# 特定のチェックのみ実行
python -m ga4_checker -p 123456789 --checks property,events

# JSONレポート出力
python -m ga4_checker -p 123456789 -o report.json

# コンソール非表示 + JSON出力のみ
python -m ga4_checker -p 123456789 -q -o report.json
```

## 設定ファイル

`config.example.yaml` をコピーして `config.yaml` を作成：

```yaml
property_id: "123456789"
credentials: "path/to/key.json"
checks:
  - property
  - events
  - custom
  - retention
```

## 定期実行

### cron

```bash
# 毎週月曜9時に実行
0 9 * * 1 cd /path/to/project && python -m ga4_checker --config config.yaml -o reports/report_$(date +\%Y\%m\%d).json
```

### GitHub Actions

`.github/workflows/ga4-audit.yml` が同梱。リポジトリの Secrets/Variables に以下を設定：

- **Secret**: `GCP_SA_KEY_PATH` - サービスアカウントキーのパス
- **Variable**: `GA4_PROPERTY_ID` - GA4 プロパティID

## 出力例

```
┌─────────────────────────────────────┐
│  GA4 設定監査レポート                │
│  プロパティID: 123456789             │
│  設定スコア: 85/100                  │
└─────────────────────────────────────┘
  OK: 8  WARNING: 3  ERROR: 0
```
