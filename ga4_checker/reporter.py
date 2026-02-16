"""監査レポート生成"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import TextIO

from ga4_checker.checks.property import CheckResult


# 日本時間
JST = timezone(timedelta(hours=9))


class Reporter:
    """チェック結果をレポートとして出力"""

    def __init__(self, property_id: str, results: list[CheckResult]):
        self.property_id = property_id
        self.results = results
        self.timestamp = datetime.now(JST)

    @property
    def summary(self) -> dict[str, int]:
        counts = {"OK": 0, "WARNING": 0, "ERROR": 0}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    @property
    def score(self) -> int:
        """設定スコア（100点満点）"""
        if not self.results:
            return 0
        total = len(self.results)
        ok = sum(1 for r in self.results if r.status == "OK")
        warning = sum(1 for r in self.results if r.status == "WARNING")
        return round((ok + warning * 0.5) / total * 100)

    def print_console(self) -> None:
        """コンソールにレポートを出力"""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            self._print_rich()
        except ImportError:
            self._print_plain()

    def _print_rich(self) -> None:
        """rich を使ったリッチ出力"""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        s = self.summary

        # ヘッダー
        console.print()
        console.print(Panel(
            f"[bold]GA4 設定監査レポート[/bold]\n"
            f"プロパティID: {self.property_id}\n"
            f"実行日時: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S JST')}\n"
            f"設定スコア: [bold]{self.score}[/bold]/100",
            title="GA4 Config Checker",
            border_style="blue",
        ))

        # サマリー
        console.print(
            f"  [green]OK: {s['OK']}[/green]  "
            f"[yellow]WARNING: {s['WARNING']}[/yellow]  "
            f"[red]ERROR: {s['ERROR']}[/red]"
        )
        console.print()

        # カテゴリ別テーブル
        categories = dict.fromkeys(r.category for r in self.results)
        for category in categories:
            table = Table(title=category, show_header=True, header_style="bold")
            table.add_column("項目", style="cyan", min_width=20)
            table.add_column("状態", justify="center", min_width=6)
            table.add_column("詳細", min_width=30)
            table.add_column("推奨アクション", min_width=30)

            for r in self.results:
                if r.category != category:
                    continue
                status_style = {
                    "OK": "[green]OK[/green]",
                    "WARNING": "[yellow]WARN[/yellow]",
                    "ERROR": "[red]ERROR[/red]",
                }
                table.add_row(
                    r.item,
                    status_style.get(r.status, r.status),
                    r.message,
                    r.recommendation or "-",
                )

            console.print(table)
            console.print()

    def _print_plain(self) -> None:
        """プレーンテキスト出力（richが無い場合）"""
        s = self.summary
        print()
        print("=" * 70)
        print("GA4 設定監査レポート")
        print(f"プロパティID: {self.property_id}")
        print(f"実行日時: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S JST')}")
        print(f"設定スコア: {self.score}/100")
        print(f"OK: {s['OK']}  WARNING: {s['WARNING']}  ERROR: {s['ERROR']}")
        print("=" * 70)

        categories = dict.fromkeys(r.category for r in self.results)
        for category in categories:
            print(f"\n--- {category} ---")
            for r in self.results:
                if r.category != category:
                    continue
                mark = {"OK": "[OK]", "WARNING": "[WARN]", "ERROR": "[ERR]"}
                print(f"  {mark.get(r.status, r.status):7s} {r.item}: {r.message}")
                if r.recommendation:
                    print(f"          -> {r.recommendation}")
        print()

    def to_json(self, fp: TextIO | None = None) -> str:
        """JSON形式でレポートを出力"""
        data = {
            "property_id": self.property_id,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
            "summary": self.summary,
            "results": [
                {
                    "category": r.category,
                    "item": r.item,
                    "status": r.status,
                    "message": r.message,
                    "recommendation": r.recommendation,
                }
                for r in self.results
            ],
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        if fp:
            fp.write(json_str)
        return json_str
