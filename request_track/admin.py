from django.contrib import admin
from django.urls import path
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib import messages
from django.utils.timezone import now, timedelta
from django.db.models import QuerySet
from django.template.response import TemplateResponse
from django.utils.html import format_html

from .models import RequestLog, IpAddress


class UserLoggedInFilter(admin.SimpleListFilter):
    """Filter for logged-in vs anonymous users."""

    title = "User Status"
    parameter_name = "user_logged_in"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        """Define filter options."""
        return (
            ("yes", "Logged-in User"),
            ("no", "Anonymous User"),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """Apply the filter."""
        if self.value() == "yes":
            return queryset.exclude(user=None)
        if self.value() == "no":
            return queryset.filter(user=None)
        return queryset


class StatusCodeFilter(admin.SimpleListFilter):
    """Filter for HTTP status code categories."""

    title = "Status Code Category"
    parameter_name = "status_category"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        """Define filter options."""
        return (
            ("2xx", "Success (2xx)"),
            ("3xx", "Redirect (3xx)"),
            ("4xx", "Client Error (4xx)"),
            ("5xx", "Server Error (5xx)"),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """Apply the filter."""
        if self.value() == "2xx":
            return queryset.filter(status_code__gte=200, status_code__lt=300)
        if self.value() == "3xx":
            return queryset.filter(status_code__gte=300, status_code__lt=400)
        if self.value() == "4xx":
            return queryset.filter(status_code__gte=400, status_code__lt=500)
        if self.value() == "5xx":
            return queryset.filter(status_code__gte=500, status_code__lt=600)
        return queryset


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    """Admin interface for RequestLog model."""

    list_display = (
        "id",
        "display_ip",
        "user",
        "app_name",
        "method",
        "truncated_route",
        "status_code",
        "requested_at",
    )
    list_filter = (
        "method",
        StatusCodeFilter,
        "requested_at",
        UserLoggedInFilter,
        "app_name",
    )
    readonly_fields = (
        "ip",
        "ip_address",
        "user",
        "user_agent",
        "route",
        "method",
        "query_params",
        "status_code",
        "requested_at",
        "app_name",
        "headers",
    )
    search_fields = ("route", "user__username", "ip__ip", "ip_address")
    date_hierarchy = "requested_at"
    list_per_page = 50
    ordering = ("-requested_at",)

    # Custom template with maintenance buttons
    change_list_template = "request_track/admin/requestlog_change_list.html"

    def display_ip(self, obj: RequestLog) -> str:
        """Display IP address, whether from relation or direct field."""
        return obj.effective_ip

    display_ip.short_description = "IP Address"

    def truncated_route(self, obj: RequestLog) -> str:
        """Show truncated route with full route on hover."""
        if len(obj.route) > 50:
            return format_html(
                '<span title="{}">{}&hellip;</span>', obj.route, obj.route[:50]
            )
        return obj.route

    truncated_route.short_description = "Route"

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding request logs manually."""
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: RequestLog | None = None
    ) -> bool:
        """Disable editing request logs."""
        return False

    def get_urls(self) -> list[path]:
        """Add custom URLs for maintenance actions."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "maintenance/",
                self.admin_site.admin_view(self.maintenance_view),
                name="requestlog-maintenance",
            ),
            path(
                "remove-older-than-week/",
                self.admin_site.admin_view(self.remove_older_than_week),
                name="requestlog-remove-week",
            ),
            path(
                "remove-older-than-month/",
                self.admin_site.admin_view(self.remove_older_than_month),
                name="requestlog-remove-month",
            ),
            path(
                "keep-last-n/",
                self.admin_site.admin_view(self.keep_last_n),
                name="requestlog-keep-last-n",
            ),
        ]
        return custom_urls + urls

    def maintenance_view(self, request: HttpRequest) -> TemplateResponse:
        """Maintenance page with various cleanup options."""
        context = {
            **self.admin_site.each_context(request),
            "title": "Request Log Maintenance",
            "log_count": RequestLog.objects.count(),
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request, "request_track/admin/requestlog_maintenance.html", context
        )

    def remove_older_than_week(self, request: HttpRequest) -> HttpResponseRedirect:
        """Remove request logs older than a week."""
        cutoff = now() - timedelta(weeks=1)
        deleted, _ = RequestLog.objects.filter(requested_at__lt=cutoff).delete()
        self.message_user(
            request,
            f"{deleted} logs older than one week were deleted.",
            messages.SUCCESS,
        )
        return HttpResponseRedirect("../")

    def remove_older_than_month(self, request: HttpRequest) -> HttpResponseRedirect:
        """Remove request logs older than a month."""
        cutoff = now() - timedelta(days=30)
        deleted, _ = RequestLog.objects.filter(requested_at__lt=cutoff).delete()
        self.message_user(
            request,
            f"{deleted} logs older than one month were deleted.",
            messages.SUCCESS,
        )
        return HttpResponseRedirect("../")

    def keep_last_n(self, request: HttpRequest) -> HttpResponseRedirect:
        """Keep only the most recent N logs."""
        try:
            n = int(request.GET.get("n", 1000))
            if n <= 0:
                raise ValueError("Must be positive")
        except ValueError:
            self.message_user(
                request,
                "Invalid value for n. Using default value of 1000.",
                messages.WARNING,
            )
            n = 1000

        ids_to_keep = RequestLog.objects.order_by("-requested_at").values_list(
            "id", flat=True
        )[:n]
        deleted, _ = RequestLog.objects.exclude(id__in=list(ids_to_keep)).delete()

        self.message_user(
            request,
            f"{deleted} logs were deleted. Only the {n} most recent logs were kept.",
            messages.SUCCESS,
        )
        return HttpResponseRedirect("../")
