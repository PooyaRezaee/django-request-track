"""
Django middleware for logging HTTP requests.

This module provides middleware for logging HTTP requests in both synchronous
and asynchronous Django applications.
"""

import random
import asyncio
from typing import Any, Callable, TypeVar

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import sync_and_async_middleware
from django.utils import timezone

import msgpack

from .models import RequestLog, IpAddress
from .settings import REQUEST_TRACK_SETTINGS, redis_client, aredis_client, redis_key
from .utils import get_ip_address

# Type variable for request handler
T = TypeVar("T")


def params_request(
    request: HttpRequest, response: HttpResponse, user
) -> dict[str, Any]:
    """
    Extract and prepare parameters from request for logging.

    Args:
        request: The Django HttpRequest object
        response: The Django HttpResponse object

    Returns:
        Dict containing all parameters needed for the RequestLog model
    """

    log_params = {
        "user_id": user.pk if user.is_authenticated else None,
        "method": request.method,
        "route": request.path,
        "status_code": response.status_code,
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
        "query_params": request.GET.urlencode(),
        "headers": get_logged_headers(request),
        "app_name": getattr(request, "current_app", None),
        "requested_at": timezone.now().isoformat(),
    }

    # Handle IP address based on configuration
    ip = get_ip_address(request)
    use_ip_model = REQUEST_TRACK_SETTINGS.get("USE_IP_ADDRESS_MODEL", True)
    if use_ip_model:
        log_params["ip_id"] = ip  # For a separate table
    else:
        log_params["ip_address"] = ip  # It is written in the same table.

    return log_params


def get_logged_headers(request: HttpRequest) -> dict[str, str]:
    """
    Extract configured headers from request.

    Args:
        request: The Django HttpRequest object

    Returns:
        Dict containing headers configured to be logged
    """
    raw_headers = REQUEST_TRACK_SETTINGS.get("HEADERS_TO_LOG", [])
    headers = {}
    for header in raw_headers:
        key = f"HTTP_{header.upper().replace('-', '_')}"
        value = request.META.get(key)
        if value:
            headers[header] = value
    return headers


def should_log_request(request: HttpRequest, user) -> bool:
    """
    Determine if the request should be logged based on configuration.

    Args:
        request: The Django HttpRequest object
        force_log_paths: List of paths that should always be logged

    Returns:
        Boolean indicating whether this request should be logged
    """
    sampling_rate = REQUEST_TRACK_SETTINGS.get("SAMPLING_RATE", 1.0)

    # Check if path is in force log paths
    force_log_paths = REQUEST_TRACK_SETTINGS.get("FORCE_PATHS", [])
    if force_log_paths and any(request.path.startswith(p) for p in force_log_paths):
        if REQUEST_TRACK_SETTINGS.get("FORCE_PATHS_SAMPLING", False):
            # Apply sampling rate if FORCE_PATHS_SAMPLING is enable
            return random.random() < sampling_rate
        else:
            return True

    # Check user logging mode
    user_logging_mode = REQUEST_TRACK_SETTINGS.get("USER_LOGGING_MODE", "all")
    user_authenticated = user.is_authenticated
    if user_logging_mode == "authenticated" and not user_authenticated:
        return False
    elif user_logging_mode == "anonymous" and user_authenticated:
        return False

    # Check exclude paths
    exclude_paths = REQUEST_TRACK_SETTINGS.get("EXCLUDE_PATHS", [])
    if "*" in exclude_paths or any(request.path.startswith(p) for p in exclude_paths):
        return False

    # Apply sampling rate
    if 0 <= sampling_rate < 1 and random.random() > sampling_rate:
        return False

    return True


@sync_and_async_middleware
def LoggingRequestMiddleware(
    get_response: Callable[[HttpRequest], T],
) -> Callable[[HttpRequest], T]:
    """
    Middleware that logs HTTP requests either via Redis buffer or direct database insert.

    This middleware supports both synchronous and asynchronous Django applications.

    Args:
        get_response: The Django request handler function

    Returns:
        Middleware function to process requests and responses
    """
    # TODO Using a buffer class to add logs to Redis in batches (with a pipeline)

    # Async middleware implementation
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: HttpRequest) -> HttpResponse:
            response = await get_response(request)
            user = await request.auser()
            if not should_log_request(request, user):
                return response

            log_params = params_request(request, response, user)

            # Choose saving method based on configuration
            if redis_client:
                packed = msgpack.dumps(log_params)
                await aredis_client.sadd(redis_key, packed)
            else:
                ip = log_params.get("ip_id")
                if ip:
                    await IpAddress.objects.aget_or_create(ip=ip)
                await RequestLog.objects.acreate(**log_params)

            return response

    # Sync middleware implementation
    else:

        def middleware(request: HttpRequest) -> HttpResponse:
            response = get_response(request)
            user = request.user
            if not should_log_request(request, user):
                return response

            log_params = params_request(request, response, user)

            # Choose saving method based on configuration
            if redis_client:
                packed = msgpack.dumps(log_params)
                redis_client.sadd(redis_key, packed)
            else:
                ip = log_params.get("ip_id")
                if ip:
                    IpAddress.objects.get_or_create(ip=ip)
                RequestLog.objects.create(**log_params)

            return response

    return middleware
