from django.contrib import admin
from .models import RequestLog

@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for the RequestLog model.
    """

    list_display = ('ip','user','route','method','status_code','requested_at')
    list_filter = ('method','status_code','requested_at')
    ordering = ("-requested_at",)
    search_fields = ('route','user_agent','ip')
