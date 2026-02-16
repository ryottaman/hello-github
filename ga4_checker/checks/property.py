"""プロパティ基本設定チェック"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ga4_checker.client import GA4Client


@dataclass
class CheckResult:
    """チェック結果"""

    category: str
    item: str
    status: str  # "OK", "WARNING", "ERROR"
    message: str
    recommendation: str = ""


class PropertyChecker:
    """GA4プロパティの基本設定をチェック"""

    CATEGORY = "プロパティ基本設定"

    # 拡張計測機能で推奨される有効項目
    RECOMMENDED_ENHANCED = {
        "scroll_tracking": "スクロール",
        "outbound_click_tracking": "離脱クリック",
        "site_search_tracking": "サイト内検索",
        "video_engagement_tracking": "動画エンゲージメント",
        "file_download_tracking": "ファイルダウンロード",
        "page_change_tracking": "ページビュー",
        "form_interaction_tracking": "フォーム操作",
    }

    def __init__(self, client: GA4Client):
        self.client = client

    def run(self) -> list[CheckResult]:
        results = []
        results.extend(self._check_property_info())
        results.extend(self._check_data_streams())
        return results

    def _check_property_info(self) -> list[CheckResult]:
        """プロパティ基本情報チェック"""
        results = []
        try:
            prop = self.client.get_property()

            # 業種設定チェック
            industry = getattr(prop, "industry_category", None)
            if not industry or str(industry) == "0":
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="業種カテゴリ",
                    status="WARNING",
                    message="業種カテゴリが未設定です",
                    recommendation="プロパティ設定で業種を設定すると、ベンチマークデータとの比較が可能になります",
                ))
            else:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="業種カテゴリ",
                    status="OK",
                    message=f"業種: {industry}",
                ))

            # タイムゾーン設定チェック
            tz = getattr(prop, "time_zone", None)
            if not tz:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="タイムゾーン",
                    status="ERROR",
                    message="タイムゾーンが未設定です",
                    recommendation="正確なレポートのためにタイムゾーンを設定してください",
                ))
            else:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="タイムゾーン",
                    status="OK",
                    message=f"タイムゾーン: {tz}",
                ))

            # 通貨設定チェック
            currency = getattr(prop, "currency_code", None)
            if not currency:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="通貨",
                    status="WARNING",
                    message="通貨が未設定です",
                    recommendation="eコマースや収益計測を使用する場合は通貨を設定してください",
                ))
            else:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="通貨",
                    status="OK",
                    message=f"通貨: {currency}",
                ))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="プロパティ情報",
                status="ERROR",
                message=f"プロパティ情報の取得に失敗: {e}",
                recommendation="プロパティIDとAPI権限を確認してください",
            ))
        return results

    def _check_data_streams(self) -> list[CheckResult]:
        """データストリーム設定チェック"""
        results = []
        try:
            streams = self.client.list_data_streams()

            if not streams:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item="データストリーム",
                    status="ERROR",
                    message="データストリームが存在しません",
                    recommendation="最低1つのデータストリームを作成してください",
                ))
                return results

            results.append(CheckResult(
                category=self.CATEGORY,
                item="データストリーム数",
                status="OK",
                message=f"{len(streams)}個のデータストリームが設定されています",
            ))

            for stream in streams:
                stream_type = str(getattr(stream, "type_", "UNKNOWN"))
                display_name = getattr(stream, "display_name", "名称未設定")

                # Webストリームの場合は拡張計測機能をチェック
                if "WEB" in stream_type:
                    results.extend(self._check_enhanced_measurement(stream))
                else:
                    results.append(CheckResult(
                        category=self.CATEGORY,
                        item=f"ストリーム: {display_name}",
                        status="OK",
                        message=f"タイプ: {stream_type}",
                    ))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item="データストリーム",
                status="ERROR",
                message=f"データストリームの取得に失敗: {e}",
            ))
        return results

    def _check_enhanced_measurement(self, stream) -> list[CheckResult]:
        """拡張計測機能チェック"""
        results = []
        display_name = getattr(stream, "display_name", "名称未設定")
        stream_name = stream.name

        try:
            settings = self.client.get_enhanced_measurement_settings(stream_name)

            if not getattr(settings, "stream_enabled", False):
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item=f"拡張計測 ({display_name})",
                    status="WARNING",
                    message="拡張計測機能が無効です",
                    recommendation="拡張計測機能を有効にすると、追加コード不要でイベントを自動収集できます",
                ))
                return results

            disabled_items = []
            for attr, label in self.RECOMMENDED_ENHANCED.items():
                if not getattr(settings, attr, False):
                    disabled_items.append(label)

            if disabled_items:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item=f"拡張計測 ({display_name})",
                    status="WARNING",
                    message=f"以下の拡張計測が無効: {', '.join(disabled_items)}",
                    recommendation="必要に応じて有効化を検討してください",
                ))
            else:
                results.append(CheckResult(
                    category=self.CATEGORY,
                    item=f"拡張計測 ({display_name})",
                    status="OK",
                    message="すべての拡張計測機能が有効です",
                ))

        except Exception as e:
            results.append(CheckResult(
                category=self.CATEGORY,
                item=f"拡張計測 ({display_name})",
                status="WARNING",
                message=f"拡張計測設定の取得に失敗: {e}",
                recommendation="API権限を確認してください",
            ))
        return results
