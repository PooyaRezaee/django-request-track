import unittest
from unittest import mock
from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from request_track.middleware import (
    LoggingRequestMiddleware,
    should_log_request,
    params_request,
    get_logged_headers,
)
from request_track.models import RequestLog, IpAddress


User = get_user_model()


class MiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.anon_user = AnonymousUser()
        
    def test_get_logged_headers(self):
        """Test that headers are correctly extracted from the request."""
        request = self.factory.get("/test-path/")
        request.META["HTTP_USER_AGENT"] = "Test Agent"
        request.META["HTTP_ACCEPT"] = "application/json"
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "HEADERS_TO_LOG": ["user-agent", "accept", "x-requested-with"]
        }):
            headers = get_logged_headers(request)
            
        self.assertEqual(headers["user-agent"], "Test Agent")
        self.assertEqual(headers["accept"], "application/json")
        self.assertEqual(headers["x-requested-with"], "XMLHttpRequest")
        
    def test_params_request(self):
        """Test that request parameters are correctly extracted."""
        request = self.factory.get("/test-path/?param1=value1&param2=value2")
        request.META["HTTP_USER_AGENT"] = "Test Agent"
        request.current_app = "test_app"
        response = HttpResponse(status=200)
        
        # Mock timezone.now() to get consistent results
        with mock.patch("django.utils.timezone.now") as mock_now:
            now = timezone.now()
            mock_now.return_value = now
            
            params = params_request(request, response, self.user)
            
        self.assertEqual(params["user_id"], self.user.pk)
        self.assertEqual(params["method"], "GET")
        self.assertEqual(params["route"], "/test-path/")
        self.assertEqual(params["status_code"], 200)
        self.assertEqual(params["user_agent"], "Test Agent")
        self.assertEqual(params["query_params"], "param1=value1&param2=value2")
        self.assertEqual(params["app_name"], "test_app")
        self.assertEqual(params["requested_at"], now.isoformat())
        
    def test_params_request_anonymous_user(self):
        """Test that request parameters handle anonymous users correctly."""
        request = self.factory.get("/test-path/")
        response = HttpResponse(status=200)
        
        params = params_request(request, response, self.anon_user)
        
        self.assertIsNone(params["user_id"])
        self.assertEqual(params["method"], "GET")
        
    def test_should_log_request_basic(self):
        """Test basic functionality of should_log_request."""
        request = self.factory.get("/test-path/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={}):
            self.assertTrue(should_log_request(request, self.user))
            
    def test_should_log_request_exclude_paths(self):
        """Test that excluded paths are not logged."""
        request = self.factory.get("/admin/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "EXCLUDE_PATHS": ["/admin/"]
        }):
            self.assertFalse(should_log_request(request, self.user))
            
    def test_should_log_request_force_paths(self):
        """Test that force paths are always logged."""
        request = self.factory.get("/api/important/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "EXCLUDE_PATHS": ["*"],  # Exclude everything
            "FORCE_PATHS": ["/api/"],  # But force log API paths
        }):
            self.assertTrue(should_log_request(request, self.user))
            
    def test_should_log_request_user_logging_mode_authenticated(self):
        """Test user logging mode for authenticated users."""
        request = self.factory.get("/test-path/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "USER_LOGGING_MODE": "authenticated"
        }):
            self.assertTrue(should_log_request(request, self.user))
            self.assertFalse(should_log_request(request, self.anon_user))
            
    def test_should_log_request_user_logging_mode_anonymous(self):
        """Test user logging mode for anonymous users."""
        request = self.factory.get("/test-path/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "USER_LOGGING_MODE": "anonymous"
        }):
            self.assertFalse(should_log_request(request, self.user))
            self.assertTrue(should_log_request(request, self.anon_user))
            
    def test_should_log_request_sampling_rate(self):
        """Test sampling rate functionality."""
        request = self.factory.get("/test-path/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "SAMPLING_RATE": 0.0  # 0% sampling rate
        }):
            self.assertFalse(should_log_request(request, self.user))
            
        with override_settings(REQUEST_TRACK_SETTINGS={
            "SAMPLING_RATE": 1.0  # 100% sampling rate
        }):
            self.assertTrue(should_log_request(request, self.user))
            
    @mock.patch('random.random')
    def test_should_log_request_force_paths_sampling(self, mock_random):
        """Test force paths with sampling enabled."""
        mock_random.return_value = 0.6  # Higher than sampling rate
        request = self.factory.get("/api/important/")
        
        with override_settings(REQUEST_TRACK_SETTINGS={
            "FORCE_PATHS": ["/api/"],
            "FORCE_PATHS_SAMPLING": True,
            "SAMPLING_RATE": 0.5  # 50% sampling rate
        }):
            self.assertFalse(should_log_request(request, self.user))
            
        mock_random.return_value = 0.4  # Lower than sampling rate
        with override_settings(REQUEST_TRACK_SETTINGS={
            "FORCE_PATHS": ["/api/"],
            "FORCE_PATHS_SAMPLING": True,
            "SAMPLING_RATE": 0.5  # 50% sampling rate
        }):
            self.assertTrue(should_log_request(request, self.user))
            
    @mock.patch('request_track.middleware.redis_client', None)
    def test_middleware_sync_without_redis(self):
        """Test synchronous middleware without Redis."""
        request = self.factory.get("/test-path/")
        request.user = self.user
        
        response_callable = mock.MagicMock(return_value=HttpResponse())
        middleware = LoggingRequestMiddleware(response_callable)
        
        # Should create a request log in the database
        initial_count = RequestLog.objects.count()
        response = middleware(request)
        
        self.assertEqual(response_callable.call_count, 1)
        self.assertEqual(RequestLog.objects.count(), initial_count + 1)
        
        log = RequestLog.objects.latest('id')
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.route, "/test-path/")
        self.assertEqual(log.user, self.user)
        
    @mock.patch('request_track.middleware.redis_client')
    def test_middleware_sync_with_redis(self, mock_redis):
        """Test synchronous middleware with Redis."""
        request = self.factory.get("/test-path/")
        request.user = self.user
        
        response_callable = mock.MagicMock(return_value=HttpResponse())
        middleware = LoggingRequestMiddleware(response_callable)
        
        # Should add log to Redis
        initial_count = RequestLog.objects.count()
        response = middleware(request)
        
        self.assertEqual(response_callable.call_count, 1)
        self.assertEqual(RequestLog.objects.count(), initial_count)  # No DB writes
        mock_redis.sadd.assert_called_once()  # Should call Redis
        
    @mock.patch('request_track.middleware.should_log_request')
    def test_middleware_skip_logging(self, mock_should_log):
        """Test middleware skips logging when should_log_request returns False."""
        mock_should_log.return_value = False
        request = self.factory.get("/test-path/")
        request.user = self.user
        
        response_callable = mock.MagicMock(return_value=HttpResponse())
        middleware = LoggingRequestMiddleware(response_callable)
        
        initial_count = RequestLog.objects.count()
        response = middleware(request)
        
        self.assertEqual(RequestLog.objects.count(), initial_count)  # No new logs