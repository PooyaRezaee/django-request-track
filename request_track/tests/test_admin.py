from django.test import TestCase
from django.contrib.auth import get_user_model
from request_track.admin import RequestLogAdmin
from request_track.models import IpAddress, RequestLog


class AdminTests(TestCase):
    def test_request_log_admin(self):
        # Create a test request log
        request_log = RequestLog.objects.create(
            ip=IpAddress.objects.create(ip="127.0.0.1"),
            user=get_user_model().objects.create_user(username="testuser", password="testpassword"),
            method="GET",
            route="/test/route/",
            status_code=200
        )

        # Create an instance of the admin class
        request_log_admin = RequestLogAdmin(model=RequestLog, admin_site=None)

        # Check the displayed fields in the admin list view
        list_display = request_log_admin.get_list_display(request_log)
        self.assertEqual(list_display, ("ip", "user", "route", "method", "status_code", "requested_at"))

        # Check the filter fields in the admin list view
        list_filter = request_log_admin.get_list_filter(request_log)
        self.assertEqual(list_filter, ("method", "status_code", "requested_at"))

        # Check the ordering in the admin list view
        ordering = request_log_admin.get_ordering(request_log)
        self.assertEqual(ordering, ("-requested_at",))

        # Check the search fields in the admin list view
        search_fields = request_log_admin.get_search_fields(request_log)
        self.assertEqual(search_fields, ("route", "user_agent", "ip"))
