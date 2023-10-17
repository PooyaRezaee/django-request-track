from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from request_track.middleware import LoggingRequestMiddleware
from django.http import HttpResponse,QueryDict
from request_track.models import RequestLog
from faker import Faker


class MiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.fake = Faker()

    def test_logging_request_middleware(self):
        # Create a test user
        user = get_user_model().objects.create_user(username=self.fake.word(), password=self.fake.word())

        # Create fake variable
        user_agent = self.fake.user_agent()

        # Create a test request
        request = self.factory.get("/",{"param_1":"value_1"})
        request.user = user
        request.META["HTTP_USER_AGENT"] = user_agent
        request.META["HTTP_X_FORWARDED_FOR"] = "127.0.0.1"
        response = HttpResponse(status=200)

        # Create an instance of the middleware and call it
        middleware = LoggingRequestMiddleware(get_response=lambda r: response)
        middleware(request)

        # Check if a RequestLog object has been created
        request_log = RequestLog.objects.first()
        self.assertIsNotNone(request_log)
        self.assertEqual(request_log.ip.ip, "127.0.0.1")
        self.assertEqual(request_log.user, user)
        self.assertEqual(request_log.method, "GET")
        self.assertEqual(request_log.route, "/")
        self.assertEqual(request_log.status_code, 200)
        self.assertIn(user_agent, request_log.user_agent)
        self.assertEqual(request_log.query_params, f"{QueryDict('param_1=value_1')}")
