from unittest import mock

from django.test import TestCase, Client, override_settings
from django.urls import path
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.views.decorators.http import require_GET, require_POST

from request_track.models import RequestLog, IpAddress


# Simple view for testing
@require_GET
def test_view(request):
    return HttpResponse("Test view")


@require_POST
def post_view(request):
    return HttpResponse("Post view", status=201)


@require_GET
def error_view(request):
    return HttpResponse("Error", status=500)


# Configure test URLs
urlpatterns = [
    path('test/', test_view, name='test_view'),
    path('post/', post_view, name='post_view'),
    path('error/', error_view, name='error_view'),
]


User = get_user_model()


@override_settings(ROOT_URLCONF=__name__)  # Use this module's URLs
class IntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={},  # Default settings
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_basic_logging(self):
        """Test that the middleware logs requests."""
        # Make request
        response = self.client.get('/test/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RequestLog.objects.count(), 1)
        
        # Verify log details
        log = RequestLog.objects.last()
        self.assertEqual(log.ip_address, None)
        self.assertIsInstance(log.ip, IpAddress)
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.route, '/test/')
        self.assertEqual(log.status_code, 200)
        self.assertIsNone(log.user)  # Anonymous user
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={},  # Default settings
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_authenticated_user(self):
        """Test middleware logging with authenticated user."""
        # Login
        self.client.login(username="testuser", password="testpassword")
        
        # Make request
        response = self.client.get('/test/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RequestLog.objects.count(), 1)
        
        # Verify log details
        log = RequestLog.objects.last()
        self.assertEqual(log.ip_address, None)
        self.assertIsInstance(log.ip, IpAddress)
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.route, '/test/')
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.user, self.user)  # Authenticated user
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "USE_IP_ADDRESS_MODEL": True
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_ip_model(self):
        """Test middleware with IP address model."""
        # Before request
        initial_ip_count = IpAddress.objects.count()
        initial_log_count = RequestLog.objects.count()
        
        # Make request with X-Forwarded-For header
        response = self.client.get(
            '/test/', 
            HTTP_X_FORWARDED_FOR='10.0.0.1'
        )
        
        # After request
        self.assertEqual(response.status_code, 200)
        self.assertEqual(IpAddress.objects.count(), initial_ip_count + 1)
        self.assertEqual(RequestLog.objects.count(), initial_log_count + 1)
        
        # Verify IP and log
        ip = IpAddress.objects.last()
        self.assertEqual(ip.ip, '10.0.0.1')
        
        log = RequestLog.objects.last()
        self.assertEqual(log.ip, ip)
        self.assertIsNone(log.ip_address)  # Should not have direct IP
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "USE_IP_ADDRESS_MODEL": False
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_direct_ip(self):
        """Test middleware with direct IP address storage."""
        # Before request
        initial_ip_count = IpAddress.objects.count()
        initial_log_count = RequestLog.objects.count()
        
        # Make request with X-Forwarded-For header
        response = self.client.get(
            '/test/', 
            HTTP_X_FORWARDED_FOR='10.0.0.1'
        )
        
        # After request
        self.assertEqual(response.status_code, 200)
        self.assertEqual(IpAddress.objects.count(), initial_ip_count)  # No new IP objects
        self.assertEqual(RequestLog.objects.count(), initial_log_count + 1)
        
        # Verify log
        log = RequestLog.objects.latest('id')
        self.assertIsNone(log.ip)  # No IP relation
        self.assertEqual(log.ip_address, '10.0.0.1')  # Direct IP
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "EXCLUDE_PATHS": ["/test/"]
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_exclude_paths(self):
        """Test that excluded paths are not logged."""
        # Before request
        initial_count = RequestLog.objects.count()
        
        # Make request to excluded path
        response = self.client.get('/test/')
        
        # After request
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RequestLog.objects.count(), initial_count)  # No new logs
        
        # Make request to non-excluded path
        response = self.client.post('/post/', {})
        
        # This should be logged
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RequestLog.objects.count(), initial_count + 1)
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "USER_LOGGING_MODE": "authenticated"
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_user_logging_mode(self):
        """Test middleware with user_logging_mode setting."""
        # Before request
        initial_count = RequestLog.objects.count()
        
        # Anonymous request (should not be logged)
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RequestLog.objects.count(), initial_count)  # No new logs
        
        # Login and make authenticated request (should be logged)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RequestLog.objects.count(), initial_count + 1)  # New log
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "HEADERS_TO_LOG": ["user-agent", "referer"]
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_headers_logging(self):
        """Test that specified headers are logged."""
        # Make request with headers
        response = self.client.get(
            '/test/',
            HTTP_USER_AGENT='Test Browser',
            HTTP_REFERER='http://example.com'
        )
        
        # Verify headers in log
        log = RequestLog.objects.latest('id')
        self.assertEqual(log.headers['user-agent'], 'Test Browser')
        self.assertEqual(log.headers['referer'], 'http://example.com')
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "FORCE_PATHS": ["/error/"],
            "SAMPLING_RATE": 0.0  # 0% sampling
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_zero_sampling_rate(self):        
        # Make request to normal path
        response = self.client.get('/test/')
        self.assertEqual(RequestLog.objects.count(), 0)
        
        # Make request to force path
        response = self.client.get('/error/')
        self.assertEqual(RequestLog.objects.count(), 1)
        
    @override_settings(
            REQUEST_TRACK_SETTINGS={
                "FORCE_PATHS": ["/error/"],
                "SAMPLING_RATE": 0.0,
                "FORCE_PATHS_SAMPLING": True
            },
            MIDDLEWARE=[
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'request_track.middleware.LoggingRequestMiddleware',
            ]
        )
    def test_middleware_zero_sampling_rate_with_force_path(self):        
        # Make request to normal path
        response = self.client.get('/test/')
        self.assertEqual(RequestLog.objects.count(), 0)
        
        # Make request to force path
        response = self.client.get('/error/')
        self.assertEqual(RequestLog.objects.count(), 0)
        
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "FORCE_PATHS": ["/error/"],
            "EXCLUDE_PATHS": ["*"]  # Exclude everything
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_force_paths(self):
        """Test middleware with force_paths setting."""
        response = self.client.get('/test/')
        self.assertEqual(RequestLog.objects.count(), 0)  # No new logs
        
        # Make request to force path
        response = self.client.get('/error/')
        self.assertEqual(RequestLog.objects.count(), 1)  # New log
        
    @mock.patch('request_track.middleware.redis_client', True)
    @mock.patch('request_track.middleware.aredis_client')
    @override_settings(
        REQUEST_TRACK_SETTINGS={
            "USE_REDIS_BUFFER": True
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'request_track.middleware.LoggingRequestMiddleware',
        ]
    )
    def test_middleware_with_redis(self, mock_aredis):
        """Test middleware with Redis buffer."""
        # Before request
        initial_count = RequestLog.objects.count()
        
        # Make request
        with mock.patch('request_track.middleware.redis_client') as mock_redis:
            response = self.client.get('/test/')
            
            # Verify no database writes but Redis call made
            self.assertEqual(response.status_code, 200)
            self.assertEqual(RequestLog.objects.count(), initial_count)  # No direct DB writes
            mock_redis.sadd.assert_called_once()  # Redis should be called