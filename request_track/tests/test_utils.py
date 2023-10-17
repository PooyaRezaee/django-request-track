import random
from django.test import RequestFactory, TestCase
from request_track.models import IpAddress
from request_track.utils import get_or_create_object_ip,get_ip_address


class UtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.ip_1 = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        self.ip_2 = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        self.ip_3 = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        self.request_1 = self.factory.get("/")
        self.request_1.META["HTTP_X_FORWARDED_FOR"] = f"{self.ip_1}, {self.ip_2}"

        self.request_2 = self.factory.get("/")
        self.request_2.META["REMOTE_ADDR"] = self.ip_3

        self.request_3 = self.factory.get("/")
        self.request_3.META["HTTP_X_FORWARDED_FOR"] = f"{self.ip_1}, {self.ip_2}"
        self.request_3.META["REMOTE_ADDR"] = self.ip_3

    def test_get_ip_by_http_x_forward_for(self):
        ip_address = get_ip_address(self.request_1)
        self.assertEqual(ip_address, self.ip_1)

    def test_get_ip_by_remote_addr(self):
        ip_address = get_ip_address(self.request_2)
        self.assertEqual(ip_address, self.ip_3)

    def test_get_ip_with_request_have_remote_addr_and_http_x(self):
        ip_address = get_ip_address(self.request_3)
        self.assertEqual(ip_address, self.ip_1)

    def test_get_or_create_object_ip(self):
        ip_obj = get_or_create_object_ip(self.ip_2)
        count_ip_addresses = IpAddress.objects.count()

        self.assertEqual(ip_obj.ip,self.ip_2)
        self.assertEqual(count_ip_addresses,1)

        # Repetition because there should be no change in re-voicing
        ip_obj = get_or_create_object_ip(self.ip_2)
        count_ip_addresses = IpAddress.objects.count()

        self.assertEqual(ip_obj.ip,self.ip_2)
        self.assertEqual(count_ip_addresses,1)
