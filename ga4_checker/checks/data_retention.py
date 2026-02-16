"""データ保持・プライバシー設定チェック"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .property import CheckResult

if TYPE_CHECKING:
    from ga4_checker.client import GA4Client


class DataRetentionChecker:
    """データ保持期間・プライバシー設定をチェック"""

    CATEGORY = "データ保持/プライバシー"

    def __init__(self, client: GA4Client):
        self.client = client

    def run(self) -> list[CheckResult]:
        results = []
        results.extend(self._check_data_retention())
        return results

    def _check_data_retention(self) -> list[CheckResult]:
        """データ保持設定チェック"""
        results = []
        try:
            settings = self.client.get_data_retention_settings()

            # イベントデータ保持期間
            retention = str(getattr(settings, "event_data_retention", ""))
            retention_label = self._retention_to_label(retention)

            if "TWO_MONTHS" in retention:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="イベントデータ保持期間",
                    status="WARNING",
                    message=f"データ保持期間: {retention_label}",
                    recommendation="探索レポートで2ヶ月以上前のデータを使用する場合は14ヶ月に変更を検討してください",
                ))
            elif "FOURTEEN_MONTHS" in retention:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="イベントデータ保持期間",
                    status="OK",
                    message=f"データ保持期間: {retention_label}",
                ))
            elif "TWENTY_SIX_MONTHS" in retention:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="イベントデータ保持期間",
                    status="OK",
                    message=f"データ保持期間: {retention_label}（360のみ）",
                ))
            elif "THIRTY_EIGHT_MONTHS" in retention:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="イベントデータ保持期間",
                    status="OK",
                    message=f"データ保持期間: {retention_label}（360のみ）",
                ))
            elif "FIFTY_MONTHS" in retention:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="イベントデータ保持期間",
                    status="OK",
                    message=f"データ保持期間: {retention_label}（360のみ）",
                ))
            else:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="イベントデータ保持期間",
                    status="WARNING",
                    message=f"データ保持期間: {retention}",
                    recommendation="データ保持期間の設定を確認してください",
                ))

            # 新規アクティビティでリセット
            reset_on_activity = getattr(settings, "reset_user_data_on_new_activity", None)
            if reset_on_activity is False:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="アクティビティでリセット",
                    status="WARNING",
                    message="「新しいアクティビティでユーザーデータのリセット」が無効です",
                    recommendation="有効にすると、ユーザーが再訪問するたびに保持期間がリセットされ、より長くデータを保持できます",
                ))
            elif reset_on_activity is True:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="アクティビティでリセット",
                    status="OK",
                    message="新しいアクティビティでデータ保持期間がリセットされます",
                ))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="データ保持設定",
                status="ERROR",
                message=f"データ保持設定の取得に失敗: {e}",
            ))
        return results

    @staticmethod
    def _retention_to_label(retention: str) -> str:
        """保持期間の列挙値をラベルに変換"""
        mapping = {
            "TWO_MONTHS": "2ヶ月",
            "FOURTEEN_MONTHS": "14ヶ月",
            "TWENTY_SIX_MONTHS": "26ヶ月",
            "THIRTY_EIGHT_MONTHS": "38ヶ月",
            "FIFTY_MONTHS": "50ヶ月",
        }
        for key, label in mapping.items():
            if key in retention:
                return label
        return retention
