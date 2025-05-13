from django.test import TestCase
from django.contrib.auth import get_user_model

from request_track.models import IpAddress, RequestLog


User = get_user_model()


class IpAddressModelTestCase(TestCase):
    def test_ip_address_creation(self):
        """Test IpAddress model creation."""
        ip = IpAddress.objects.create(ip="192.168.1.1")
        self.assertEqual(str(ip), "192.168.1.1")
        self.assertTrue(IpAddress.objects.filter(ip="192.168.1.1").exists())
        
    def test_ip_address_unique(self):
        """Test IP addresses are unique."""
        ip1 = IpAddress.objects.create(ip="192.168.1.1")
        # Creating the same IP should fail with IntegrityError
        with self.assertRaises(Exception):  # Should raise some form of integrity constraint error
            ip2 = IpAddress.objects.create(ip="192.168.1.1")
            
    def test_ip_address_ipv6(self):
        """Test IPv6 address support."""
        ipv6 = IpAddress.objects.create(ip="2001:db8::1")
        self.assertEqual(str(ipv6), "2001:db8::1")
        self.assertTrue(IpAddress.objects.filter(ip="2001:db8::1").exists())


class RequestLogModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.ip = IpAddress.objects.create(ip="192.168.1.1")
        
    def test_requestlog_creation_with_ip_model(self):
        """Test RequestLog creation with IP Address model reference."""
        log = RequestLog.objects.create(
            ip=self.ip,
            user=self.user,
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="param1=value1",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00",
            app_name="test_app",
            headers={"user-agent": "Test Agent"}
        )
        
        self.assertEqual(log.ip, self.ip)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.route, "/test/")
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.app_name, "test_app")
        self.assertEqual(log.headers["user-agent"], "Test Agent")
        
    def test_requestlog_creation_with_direct_ip(self):
        """Test RequestLog creation with direct IP address field."""
        log = RequestLog.objects.create(
            ip_address="192.168.1.2",
            user=self.user,
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="param1=value1",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        self.assertIsNone(log.ip)
        self.assertEqual(log.ip_address, "192.168.1.2")
        self.assertEqual(log.method, "GET")
        
    def test_requestlog_creation_anonymous_user(self):
        """Test RequestLog creation with anonymous user."""
        log = RequestLog.objects.create(
            ip=self.ip,
            user=None,  # Anonymous user
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        self.assertIsNone(log.user)
        self.assertEqual(log.ip, self.ip)
        
    def test_effective_ip_with_ip_model(self):
        """Test effective_ip property with IP model."""
        log = RequestLog.objects.create(
            ip=self.ip,
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        self.assertEqual(log.effective_ip, "192.168.1.1")
        
    def test_effective_ip_with_direct_ip(self):
        """Test effective_ip property with direct IP."""
        log = RequestLog.objects.create(
            ip_address="192.168.1.2",
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        self.assertEqual(log.effective_ip, "192.168.1.2")
        
    def test_effective_ip_with_no_ip(self):
        """Test effective_ip property with no IP information."""
        log = RequestLog.objects.create(
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        self.assertEqual(log.effective_ip, "Unknown")
        
    def test_string_representation(self):
        """Test RequestLog string representation."""
        log = RequestLog.objects.create(
            ip=self.ip,
            user=self.user,
            user_agent="Test Agent",
            route="/test/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        expected = f"{self.ip} - {self.user} - /test/ - 200"
        self.assertEqual(str(log), expected)
        
    def test_ordering(self):
        """Test RequestLog ordering is by requested_at descending."""
        log1 = RequestLog.objects.create(
            user_agent="Test Agent",
            route="/test1/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-01T12:00:00+00:00"
        )
        
        log2 = RequestLog.objects.create(
            user_agent="Test Agent",
            route="/test2/",
            method="GET",
            query_params="",
            status_code=200,
            requested_at="2023-01-02T12:00:00+00:00"
        )
        
        # First item should be the most recent
        self.assertEqual(RequestLog.objects.first(), log2)
        self.assertEqual(RequestLog.objects.last(), log1)