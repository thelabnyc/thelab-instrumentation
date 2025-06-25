from __future__ import annotations

from typing import TYPE_CHECKING, Any
import logging

from botocore.exceptions import BotoCoreError, ClientError
import boto3

from .base import MetricData, MetricsBackend

if TYPE_CHECKING:
    from mypy_boto3_cloudwatch import CloudWatchClient
    from mypy_boto3_cloudwatch.type_defs import MetricDatumTypeDef

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

    def send_metrics(
        self,
        metrics: list[MetricData],
    ) -> None:
        assert len(metrics) <= 1000  # TODO: autobatch this case.
        cw_batch = []
        for metric in metrics:
            datum: MetricDatumTypeDef = {
                "MetricName": metric["name"],
                "Value": metric["value"],
                "Unit": metric.get("unit") or "None",
            }
            timestamp = metric.get("timestamp")
            if timestamp:
                datum["Timestamp"] = timestamp
            dimensions = self._get_all_dimensions(metric.get("dimensions"))
            if dimensions:
                datum["Dimensions"] = [
                    {"Name": name, "Value": value} for name, value in dimensions.items()
                ]
            cw_batch.append(datum)
        self._send_batch(cw_batch)

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
