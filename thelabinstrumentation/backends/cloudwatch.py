from datetime import datetime
from typing import TYPE_CHECKING, Any
import logging

from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_cloudwatch import CloudWatchClient
from mypy_boto3_cloudwatch.literals import StandardUnitType
from mypy_boto3_cloudwatch.type_defs import MetricDatumTypeDef
import boto3

from .base import MetricsBackend

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch.literals import StandardUnitType
else:
    StandardUnitType = str

logger = logging.getLogger(__name__)


class CloudWatchBackend(MetricsBackend):
    """CloudWatch metrics backend implementation."""

    client: CloudWatchClient

    def __init__(
        self,
        namespace: str,
        **kwargs: Any,
    ) -> None:
        self.namespace = namespace
        self.client = boto3.client("cloudwatch", **kwargs)

    def send_metric(
        self,
        metric_name: str,
        value: float,
        unit: StandardUnitType | None = None,
        dimensions: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Send a single metric to CloudWatch."""
        datum: MetricDatumTypeDef = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit or "None",
        }
        # Add timestamp if provided - convert float to datetime
        if timestamp:
            datum["Timestamp"] = timestamp

        # Add dimensions if provided
        if dimensions:
            datum["Dimensions"] = [
                {"Name": name, "Value": value}
                for name, value in self._get_all_dimensions(dimensions).items()
            ]
        self._send_batch([datum])

    def _send_batch(self, metric_data: list[MetricDatumTypeDef]) -> None:
        """Send a batch of metrics to CloudWatch."""
        try:
            response = self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data,
            )
            logger.debug(f"Successfully sent {len(metric_data)} metrics to CloudWatch")

            # Log any failures from the response
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
                logger.warning(f"CloudWatch response: {response}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"CloudWatch ClientError [{error_code}]: {error_message}")
        except BotoCoreError as e:
            logger.error(f"CloudWatch BotoCoreError: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending metrics to CloudWatch: {e}")
