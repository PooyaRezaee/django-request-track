from django.test import TestCase, RequestFactory

from request_track.utils import get_ip_address


class UtilsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
    def test_get_ip_address_from_remote_addr(self):
        """Test getting IP from REMOTE_ADDR."""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        
        ip = get_ip_address(request)
        self.assertEqual(ip, "192.168.1.1")
        
    def test_get_ip_address_from_x_forwarded_for(self):
        """Test getting IP from X-Forwarded-For header."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1"
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        
        ip = get_ip_address(request)
        self.assertEqual(ip, "10.0.0.1")
        
    def test_get_ip_address_from_x_forwarded_for_multiple(self):
        """Test getting IP from X-Forwarded-For with multiple IPs."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2, 10.0.0.3"
        
        ip = get_ip_address(request)
        self.assertEqual(ip, "10.0.0.1")  # Should get the first IP
        
    def test_get_ip_address_with_empty_request(self):
        """Test getting IP with empty request."""
        request = self.factory.get("/")
        request.META.pop('REMOTE_ADDR', None)
        request.META.pop('HTTP_X_FORWARDED_FOR', None)
        # No REMOTE_ADDR or X-Forwarded-For

        ip = get_ip_address(request)
        self.assertEqual(ip, "")  # Should return empty string
        
    def test_get_ip_address_ipv6(self):
        """Test getting IPv6 address."""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "2001:db8::1"
        
        ip = get_ip_address(request)
        self.assertEqual(ip, "2001:db8::1")