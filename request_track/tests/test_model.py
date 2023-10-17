import random
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import QueryDict
from faker import Faker
from request_track.models import RequestLog,IpAddress


class ModelTests(TestCase):
    def setUp(self):
        self.fake = Faker()

        self.user = get_user_model().objects.create_user(
            username=self.fake.word(),
            password=self.fake.word(),
        )

        # Fake variable
        self.ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        self.user_agent = self.fake.user_agent()
        self.route = "/"
        self.method = "GET"
        self.status_code = 200
        self.query_params = QueryDict("param1=value1&param2=value2")

        # Test objects
        self.ip_address = IpAddress.objects.create(ip=self.ip)
        self.request_log = RequestLog.objects.create(
            ip=self.ip_address,
            user=self.user,
            user_agent=self.user_agent,
            route=self.route,
            method=self.method,
            query_params=self.query_params,
            status_code=self.status_code
        )

    def test_ip_address_str(self):
        self.assertEqual(str(self.ip_address), self.ip)

    def test_request_log_str(self):
        expected_str = f"{self.ip_address} - {self.user} - {self.route} - {self.status_code} - {self.request_log.requested_at}"
        self.assertEqual(str(self.request_log), expected_str)

    def test_request_log_creation(self):
        self.assertEqual(self.request_log.ip, self.ip_address)
        self.assertEqual(self.request_log.user, self.user)
        self.assertEqual(self.request_log.user_agent, self.user_agent)
        self.assertEqual(self.request_log.route, self.route)
        self.assertEqual(self.request_log.method, self.method)
        self.assertEqual(self.request_log.query_params, self.query_params)
        self.assertEqual(self.request_log.status_code, self.status_code)

    def test_request_log_verbose_name(self):
        self.assertEqual(RequestLog._meta.verbose_name, "Requests Log")

    def test_request_log_related_name(self):
        self.assertEqual(self.ip_address.log.first(), self.request_log)

    def test_request_log_null_user(self):
        request_log_null_user = RequestLog.objects.create(
            ip=self.ip_address,
            user=None,
            user_agent=self.user_agent,
            route=self.route,
            method=self.method,
            query_params=self.query_params,
            status_code=self.status_code
        )

        self.assertIsNone(request_log_null_user.user)
