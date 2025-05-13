from unittest import mock
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone

from request_track.admin import RequestLogAdmin, UserLoggedInFilter, StatusCodeFilter
from request_track.models import RequestLog, IpAddress


User = get_user_model()


class MockSuperUser:
    """Mock admin superuser for testing."""
    is_active = True
    is_staff = True
    is_superuser = True
    
    def has_perm(self, perm, obj=None):
        return True


class AdminTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = RequestLogAdmin(RequestLog, self.site)
        
        # Create a superuser
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword"
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        
        # Create IP address
        self.ip = IpAddress.objects.create(ip="192.168.1.1")
        
        # Create request logs
        self.log1 = RequestLog.objects.create(
            ip=self.ip,
            user=self.user,
            user_agent="Test Agent",
            route="/test1/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at=timezone.now() - timezone.timedelta(days=10)
        )
        
        self.log2 = RequestLog.objects.create(
            ip=self.ip,
            user=None,  # Anonymous
            user_agent="Test Agent",
            route="/test2/",
            method="POST",
            query_params="",
            status_code=404,
            requested_at=timezone.now() - timezone.timedelta(days=5)
        )
        
        self.log3 = RequestLog.objects.create(
            ip=self.ip,
            user=self.user,
            user_agent="Test Agent",
            route="/test3/",
            method="GET",
            query_params="",
            status_code=500,
            requested_at=timezone.now()
        )
        
    def test_display_ip(self):
        """Test display_ip method."""
        self.assertEqual(self.admin.display_ip(self.log1), "192.168.1.1")
        
    def test_truncated_route_short(self):
        """Test truncated_route method with short route."""
        self.assertEqual(self.admin.truncated_route(self.log1), "/test1/")
        
    def test_truncated_route_long(self):
        """Test truncated_route method with long route."""
        long_route = "/very/long/route/" * 10  # Over 50 chars
        log = RequestLog.objects.create(
            user_agent="Test Agent",
            route=long_route, 
            method="GET",
            query_params="",
            status_code=200,
            requested_at=timezone.now()
        )
        
        truncated = self.admin.truncated_route(log)
        self.assertIn("&hellip;", truncated)  # Should contain ellipsis
        
    def test_has_add_permission(self):
        """Test has_add_permission method."""
        request = self.factory.get("/admin/request_track/requestlog/add/")
        request.user = self.superuser
        
        self.assertFalse(self.admin.has_add_permission(request))
        
    def test_has_change_permission(self):
        """Test has_change_permission method."""
        request = self.factory.get("/admin/request_track/requestlog/1/change/")
        request.user = self.superuser
        
        self.assertFalse(self.admin.has_change_permission(request, self.log1))        