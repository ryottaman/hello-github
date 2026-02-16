"""カスタム定義（ディメンション・指標・ユーザープロパティ）チェック"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .property import CheckResult

if TYPE_CHECKING:
    from ga4_checker.client import GA4Client


# GA4のカスタム定義の上限
LIMITS = {
    "event_scoped_dimensions": 50,
    "user_scoped_dimensions": 25,
    "custom_metrics": 50,
}


class CustomDefinitionsChecker:
    """カスタムディメンション・カスタム指標の設定をチェック"""

    CATEGORY = "カスタム定義"

    def __init__(self, client: GA4Client):
        self.client = client

    def run(self) -> list[CheckResult]:
        results = []
        results.extend(self._check_custom_dimensions())
        results.extend(self._check_custom_metrics())
        return results

    def _check_custom_dimensions(self) -> list[CheckResult]:
        """カスタムディメンションのチェック"""
        results = []
        try:
            dimensions = self.client.list_custom_dimensions()

            if not dimensions:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="カスタムディメンション",
                    status="WARNING",
                    message="カスタムディメンションが未設定です",
                    recommendation="ビジネス固有の分析軸がある場合はカスタムディメンションの設定を検討してください",
                ))
                return results

            # スコープ別に分類
            event_scoped = []
            user_scoped = []
            for dim in dimensions:
                scope = str(getattr(dim, "scope", ""))
                display_name = getattr(dim, "display_name", "名称未設定")
                param_name = getattr(dim, "parameter_name", "")
                if "USER" in scope:
                    user_scoped.append((display_name, param_name))
                else:
                    event_scoped.append((display_name, param_name))

            # イベントスコープの使用状況
            event_limit = LIMITS["event_scoped_dimensions"]
            event_usage = len(event_scoped) / event_limit * 100
            results.append(CheckResult(
                category=self.CATEGORY,
                item="イベントスコープ ディメンション",
                status="WARNING" if event_usage >= 80 else "OK",
                message=f"{len(event_scoped)}/{event_limit}個使用中 ({event_usage:.0f}%)",
                recommendation="上限に近づいています。不要なディメンションの整理を検討してください" if event_usage >= 80 else "",
            ))

            # ユーザースコープの使用状況
            user_limit = LIMITS["user_scoped_dimensions"]
            user_usage = len(user_scoped) / user_limit * 100
            results.append(CheckResult(
                category=self.CATEGORY,
                item="ユーザースコープ ディメンション",
                status="WARNING" if user_usage >= 80 else "OK",
                message=f"{len(user_scoped)}/{user_limit}個使用中 ({user_usage:.0f}%)",
                recommendation="上限に近づいています。不要なディメンションの整理を検討してください" if user_usage >= 80 else "",
            ))

            # 命名規則チェック
            results.extend(self._check_dimension_naming(dimensions))

            # 説明文の有無チェック
            no_description = [
                getattr(d, "display_name", "")
                for d in dimensions
                if not getattr(d, "description", "")
            ]
            if no_description:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="ディメンション説明文",
                    status="WARNING",
                    message=f"{len(no_description)}個のディメンションに説明文がありません",
                    recommendation="説明文を追加すると、チームメンバーが各ディメンションの用途を理解しやすくなります",
                ))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="カスタムディメンション",
                status="ERROR",
                message=f"カスタムディメンションの取得に失敗: {e}",
            ))
        return results

    def _check_custom_metrics(self) -> list[CheckResult]:
        """カスタム指標のチェック"""
        results = []
        try:
            metrics = self.client.list_custom_metrics()

            if not metrics:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="カスタム指標",
                    status="OK",
                    message="カスタム指標は未設定です（必須ではありません）",
                ))
                return results

            limit = LIMITS["custom_metrics"]
            usage = len(metrics) / limit * 100
            results.append(CheckResult(
                category=self.CATEGORY,
                item="カスタム指標",
                status="WARNING" if usage >= 80 else "OK",
                message=f"{len(metrics)}/{limit}個使用中 ({usage:.0f}%)",
                recommendation="上限に近づいています。不要な指標の整理を検討してください" if usage >= 80 else "",
            ))

            # 計測単位のチェック
            for metric in metrics:
                display_name = getattr(metric, "display_name", "名称未設定")
                unit = str(getattr(metric, "measurement_unit", ""))
                if "UNSPECIFIED" in unit or not unit:
                    results.append(CheckResult(
                        category=self.CATEGORY,
                        item=f"指標: {display_name}",
                        status="WARNING",
                        message="計測単位が未指定です",
                        recommendation="適切な計測単位（STANDARD, CURRENCY, FEET, METERS, etc.）を設定してください",
                    ))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="カスタム指標",
                status="ERROR",
                message=f"カスタム指標の取得に失敗: {e}",
            ))
        return results

    def _check_dimension_naming(self, dimensions) -> list[CheckResult]:
        """ディメンション名の命名規則チェック"""
        results = []
        issues = []

        for dim in dimensions:
            param_name = getattr(dim, "parameter_name", "")
            display_name = getattr(dim, "display_name", "")

            if not param_name:
                continue

            if len(param_name) > 40:
                issues.append(f"{display_name} (パラメータ名が40文字超過)")
            elif param_name != param_name.lower():
                issues.append(f"{display_name} (パラメータ名に大文字)")
            elif param_name.startswith(("ga_", "google_", "firebase_")):
                issues.append(f"{display_name} (予約プレフィックス)")

        if issues:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="ディメンション命名規則",
                status="WARNING",
                message=f"命名規則に問題: {', '.join(issues)}",
                recommendation="パラメータ名はsnake_caseかつ40文字以内を推奨",
            ))

        return results
