from django.db import models
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property


class IpAddress(models.Model):
    """
    Represents an IP address from HTTP requests.

    This model stores unique IP addresses to optimize database storage
    by avoiding repeated storage of the same IP strings.

    Attributes:
        ip: The IP address string (IPv4 or IPv6)
    """

    ip = models.GenericIPAddressField(
        unique=True, verbose_name="IP Address", help_text="IPv4 or IPv6 address"
    )

    class Meta:
        verbose_name = "IP Address"
        verbose_name_plural = "IP Addresses"

    def __str__(self) -> str:
        return str(self.ip)


class RequestLog(models.Model):
    """
    Stores detailed information about HTTP requests.

    This model records details about HTTP requests including IP address,
    user information, route, status code, and other metadata.

    Attributes:
        ip: Foreign key to IpAddress model (used when USE_IP_ADDRESS_MODEL=True)
        ip_address: Direct IP address string (used when USE_IP_ADDRESS_MODEL=False)
        user: The authenticated user who made the request (null for anonymous)
        user_agent: Browser/client user agent string
        route: The requested URL path
        method: The HTTP method (GET, POST, etc.)
        query_params: URL query parameters
        status_code: HTTP response status code
        requested_at: Timestamp when the request was made
        app_name: Django application name if available
        headers: JSON field for storing logged request headers
    """

    ip = models.ForeignKey(
        IpAddress,
        on_delete=models.CASCADE,
        related_name="log",
        to_field="ip",
        null=True,
        blank=True,
        verbose_name="IP Address",
        help_text="Reference to IP address object",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Direct IP Address",
        help_text="IP address stored directly (when IP model is disabled)",
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="User",
        help_text="User who made the request (if authenticated)",
    )
    user_agent = models.CharField(
        max_length=300,
        verbose_name="User Agent",
        help_text="Browser or client information",
    )
    route = models.CharField(
        max_length=1000,
        db_index=True,
        verbose_name="Route",
        help_text="URL path that was requested",
    )
    method = models.CharField(
        max_length=10, verbose_name="Method", help_text="HTTP method (GET, POST, etc.)"
    )
    query_params = models.TextField(
        verbose_name="Query Parameters", help_text="URL query string parameters"
    )
    status_code = models.PositiveIntegerField(
        db_index=True, verbose_name="Status Code", help_text="HTTP response status code"
    )
    requested_at = models.DateTimeField(
        db_index=True,
        verbose_name="Requested At",
        help_text="Timestamp when the request was made",
    )
    app_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="App Name",
        help_text="Django application name if available",
    )
    headers = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Headers",
        help_text="Selected HTTP headers from the request",
    )

    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["requested_at", "status_code"]),
            models.Index(fields=["method", "status_code"]),
        ]

    def __str__(self) -> str:
        ip_display = self.ip or self.ip_address or "Unknown IP"
        user_display = self.user or "Anonymous"
        return f"{ip_display} - {user_display} - {self.route} - {self.status_code}"

    @cached_property
    def effective_ip(self) -> str:
        """Return the effective IP address regardless of storage method."""
        if self.ip:
            return str(self.ip.ip)
        elif self.ip_address:
            return str(self.ip_address)
        else:
            return "Unknown"
