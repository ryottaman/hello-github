"""イベント・コンバージョン設定チェック"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .property import CheckResult

if TYPE_CHECKING:
    from ga4_checker.client import GA4Client


# GA4で推奨されるコンバージョンイベント（業種共通）
RECOMMENDED_CONVERSIONS = {
    "purchase": "購入完了",
    "generate_lead": "リード獲得",
    "sign_up": "会員登録",
    "begin_checkout": "チェックアウト開始",
    "add_to_cart": "カート追加",
    "first_open": "初回起動（アプリ）",
}

# GA4推奨イベント
RECOMMENDED_EVENTS_ECOMMERCE = [
    "view_item",
    "add_to_cart",
    "begin_checkout",
    "purchase",
    "view_item_list",
    "select_item",
    "add_payment_info",
    "add_shipping_info",
    "refund",
]

RECOMMENDED_EVENTS_ENGAGEMENT = [
    "login",
    "sign_up",
    "share",
    "search",
    "select_content",
]


class EventChecker:
    """イベント・コンバージョン設定をチェック"""

    CATEGORY = "イベント/コンバージョン"

    def __init__(self, client: GA4Client):
        self.client = client

    def run(self) -> list[CheckResult]:
        results = []
        results.extend(self._check_conversion_events())
        return results

    def _check_conversion_events(self) -> list[CheckResult]:
        """コンバージョンイベントの設定チェック"""
        results = []
        try:
            conversions = self.client.list_conversion_events()
            conversion_names = {
                getattr(c, "event_name", "") for c in conversions
            }

            if not conversions:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="コンバージョン設定",
                    status="ERROR",
                    message="コンバージョンイベントが1つも設定されていません",
                    recommendation="ビジネス目標に合わせてコンバージョンイベントを設定してください",
                ))
            else:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="コンバージョン数",
                    status="OK",
                    message=f"{len(conversions)}個のコンバージョンイベントが設定済み",
                ))

                # 設定済みコンバージョンの一覧
                names_list = ", ".join(sorted(conversion_names))
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="コンバージョン一覧",
                    status="OK",
                    message=f"設定済み: {names_list}",
                ))

            # 上限チェック（GA4は最大30個）
            if len(conversions) >= 30:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="コンバージョン上限",
                    status="WARNING",
                    message="コンバージョンイベントが上限(30個)に達しています",
                    recommendation="不要なコンバージョンを整理してください",
                ))

            # 推奨コンバージョンの未設定チェック
            missing = []
            for event_name, label in RECOMMENDED_CONVERSIONS.items():
                if event_name not in conversion_names:
                    missing.append(f"{event_name} ({label})")

            if missing:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="推奨コンバージョン",
                    status="WARNING",
                    message=f"以下の推奨コンバージョンが未設定: {', '.join(missing)}",
                    recommendation="ビジネスに該当するものがあれば設定を検討してください（すべて必須ではありません）",
                ))

            # カスタムイベント名の命名規則チェック
            results.extend(self._check_event_naming(conversions))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="コンバージョン",
                status="ERROR",
                message=f"コンバージョンイベントの取得に失敗: {e}",
            ))
        return results

    def _check_event_naming(self, conversions) -> list[CheckResult]:
        """イベント名の命名規則チェック"""
        results = []
        bad_names = []

        for conv in conversions:
            name = getattr(conv, "event_name", "")
            if not name:
                continue

            # GA4推奨の命名規則: snake_case、40文字以内
            if len(name) > 40:
                bad_names.append(f"{name} (40文字超過)")
            elif name != name.lower():
                bad_names.append(f"{name} (大文字を含む)")
            elif " " in name:
                bad_names.append(f"{name} (スペースを含む)")
            elif name.startswith(("ga_", "google_", "firebase_")):
                bad_names.append(f"{name} (予約プレフィックス)")

        if bad_names:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="イベント命名規則",
                status="WARNING",
                message=f"命名規則に問題があるイベント: {', '.join(bad_names)}",
                recommendation="GA4ではsnake_caseかつ40文字以内の命名を推奨。ga_/google_/firebase_プレフィックスは予約済み",
            ))
        else:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="イベント命名規則",
                status="OK",
                message="すべてのイベント名が命名規則に準拠しています",
            ))

        return results
