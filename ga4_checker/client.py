"""GA4 Admin API クライアントラッパー"""

from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import (
    ListDataStreamsRequest,
    GetDataRetentionSettingsRequest,
    ListCustomDimensionsRequest,
    ListCustomMetricsRequest,
    ListConversionEventsRequest,
)
from google.auth import default as auth_default
from google.oauth2 import service_account


class GA4Client:
    """Google Analytics 4 Admin API のクライアント"""

    def __init__(self, property_id: str, credentials_path: str | None = None):
        self.property_id = property_id
        self.property_name = f"properties/{property_id}"

        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
            self.client = AnalyticsAdminServiceClient(credentials=credentials)
        else:
            credentials, _ = auth_default(
                scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            self.client = AnalyticsAdminServiceClient(credentials=credentials)

    def get_property(self):
        """プロパティ情報を取得"""
        return self.client.get_property(name=self.property_name)

    def list_data_streams(self):
        """データストリーム一覧を取得"""
        request = ListDataStreamsRequest(parent=self.property_name)
        return list(self.client.list_data_streams(request=request))

    def get_enhanced_measurement_settings(self, stream_name: str):
        """拡張計測機能の設定を取得"""
        return self.client.get_enhanced_measurement_settings(name=f"{stream_name}/enhancedMeasurementSettings")

    def list_conversion_events(self):
        """コンバージョンイベント一覧を取得"""
        request = ListConversionEventsRequest(parent=self.property_name)
        return list(self.client.list_conversion_events(request=request))

    def list_custom_dimensions(self):
        """カスタムディメンション一覧を取得"""
        request = ListCustomDimensionsRequest(parent=self.property_name)
        return list(self.client.list_custom_dimensions(request=request))

    def list_custom_metrics(self):
        """カスタム指標一覧を取得"""
        request = ListCustomMetricsRequest(parent=self.property_name)
        return list(self.client.list_custom_metrics(request=request))

    def get_data_retention_settings(self):
        """データ保持設定を取得"""
        request = GetDataRetentionSettingsRequest(
            name=f"{self.property_name}/dataRetentionSettings"
        )
        return self.client.get_data_retention_settings(request=request)
