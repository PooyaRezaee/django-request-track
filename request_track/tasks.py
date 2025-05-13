"""
Celery tasks for processing request logs from Redis buffer.
"""

from django.conf import settings

import redis
import msgpack
from celery import shared_task

from .models import RequestLog, IpAddress
from .settings import REQUEST_TRACK_SETTINGS, redis_client, redis_key


@shared_task
def process_request_logs(max_items: int | None = None) -> dict[str, int]:
    """
    Process request logs from Redis buffer and save them to the database.

    This task fetches log entries from Redis, processes them, and bulk inserts
    them into the database for better performance.

    Args:
        max_items: Maximum number of items to process in one batch (None for all)

    Returns:
        Dict with counts of processed logs and IPs
    """
    if redis_client is None:
        return {"error": "Redis client not configured"}

    # Use pipeline for atomic operations
    pipe = redis_client.pipeline()
    if max_items:
        pipe.spop(redis_key, max_items)
    else:
        pipe.smembers(redis_key)
        pipe.delete(redis_key)

    items, _ = pipe.execute()

    if not items:
        return None

    # Deserialize all logs
    logs = [msgpack.loads(raw) for raw in items]

    # Extract unique IPs (if exists ip_id)
    ip_set = set()
    for log in filter(lambda log: log.get("ip_id"), logs):
        ip_set.add(log["ip_id"])

    # Find which IPs already exist in database
    if ip_set:
        existing_ips = set(
            IpAddress.objects.filter(ip__in=ip_set).values_list("ip", flat=True)
        )
        missing_ips = ip_set - existing_ips

        # Create missing IPs
        if missing_ips:
            IpAddress.objects.bulk_create(
                [IpAddress(ip=ip) for ip in missing_ips], ignore_conflicts=True
            )

    # Bulk create logs
    RequestLog.objects.bulk_create([RequestLog(**log) for log in logs])
