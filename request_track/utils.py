"""
Utility functions for request logging.
"""

from django.http import HttpRequest


def get_ip_address(request: HttpRequest) -> str:
    """
    Extract client IP address from request, handling proxy headers.

    Args:
        request: The Django HttpRequest object

    Returns:
        String containing the client IP address
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "")
