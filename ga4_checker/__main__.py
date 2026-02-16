"""GA4 Config Checker - CLI エントリポイント

使い方:
    python -m ga4_checker --property-id 123456789
    python -m ga4_checker --property-id 123456789 --credentials sa-key.json
    python -m ga4_checker --config config.yaml
    python -m ga4_checker --property-id 123456789 --checks property,events --output report.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from ga4_checker.client import GA4Client
from ga4_checker.checks import (
    PropertyChecker,
    EventChecker,
    CustomDefinitionsChecker,
    DataRetentionChecker,
)
from ga4_checker.checks.property import CheckResult
from ga4_checker.reporter import Reporter


AVAILABLE_CHECKS = {
    "property": ("プロパティ基本設定", PropertyChecker),
    "events": ("イベント/コンバージョン", EventChecker),
    "custom": ("カスタム定義", CustomDefinitionsChecker),
    "retention": ("データ保持/プライバシー", DataRetentionChecker),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ga4_checker",
        description="GA4 設定監査チェッカー - プロパティの設定を自動チェックしてレポートを生成",
    )
    parser.add_argument(
        "--property-id", "-p",
        help="GA4 プロパティID (例: 123456789)",
    )
    parser.add_argument(
        "--credentials", "-c",
        help="サービスアカウントキーのJSONファイルパス（省略時はADCを使用）",
    )
    parser.add_argument(
        "--config",
        help="YAML設定ファイルのパス",
    )
    parser.add_argument(
        "--checks",
        help=f"実行するチェックをカンマ区切りで指定 (選択肢: {', '.join(AVAILABLE_CHECKS.keys())})",
        default=",".join(AVAILABLE_CHECKS.keys()),
    )
    parser.add_argument(
        "--output", "-o",
        help="JSON レポートの出力先ファイルパス",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="コンソール出力を抑制（JSON出力のみ）",
    )
    return parser.parse_args(argv)


def load_config(config_path: str) -> dict:
    """YAML設定ファイルを読み込み"""
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_checks(client: GA4Client, check_names: list[str]) -> list[CheckResult]:
    """指定されたチェックを実行"""
    results: list[CheckResult] = []
    for name in check_names:
        name = name.strip()
        if name not in AVAILABLE_CHECKS:
            print(f"WARNING: 不明なチェック名 '{name}' をスキップ", file=sys.stderr)
            continue
        label, checker_cls = AVAILABLE_CHECKS[name]
        print(f"  チェック中: {label}...", file=sys.stderr)
        checker = checker_cls(client)
        results.extend(checker.run())
    return results


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # 設定の解決: --config が指定されていればそちらを優先
    property_id = args.property_id
    credentials = args.credentials
    check_names = args.checks.split(",")

    if args.config:
        config = load_config(args.config)
        property_id = property_id or config.get("property_id")
        credentials = credentials or config.get("credentials")
        if "checks" in config:
            check_names = config["checks"]

    if not property_id:
        print("ERROR: --property-id または --config で GA4 プロパティIDを指定してください", file=sys.stderr)
        return 1

    # クライアント初期化
    print(f"GA4 設定チェッカー - プロパティ: {property_id}", file=sys.stderr)
    try:
        client = GA4Client(property_id, credentials)
    except Exception as e:
        print(f"ERROR: API クライアントの初期化に失敗: {e}", file=sys.stderr)
        return 1

    # チェック実行
    results = run_checks(client, check_names)

    # レポート出力
    reporter = Reporter(property_id, results)

    if not args.quiet:
        reporter.print_console()

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            reporter.to_json(f)
        print(f"レポートを保存しました: {output_path}", file=sys.stderr)

    # エラーがあれば終了コード1
    if reporter.summary.get("ERROR", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
