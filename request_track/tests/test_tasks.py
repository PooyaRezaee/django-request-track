from unittest import mock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

import msgpack

from request_track.tasks import process_request_logs
from request_track.models import RequestLog, IpAddress


User = get_user_model()


class TasksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        
        # Sample log data
        self.log_data_with_ip = {
            "ip_id": "192.168.1.1",  # IP relation
            "user_id": self.user.id,
            "method": "GET",
            "route": "/test/",
            "status_code": 200,
            "user_agent": "Test Agent",
            "query_params": "param1=value1",
            "requested_at": "2023-01-01T12:00:00+00:00",
            "app_name": "test_app",
            "headers": {"user-agent": "Test Agent"}
        }
        
        self.log_data_with_direct_ip = {
            "ip_address": "192.168.1.2",  # Direct IP
            "user_id": None,
            "method": "POST",
            "route": "/api/",
            "status_code": 201,
            "user_agent": "API Client",
            "query_params": "param2=value2",
            "requested_at": "2023-01-01T12:30:00+00:00",
            "app_name": "api",
            "headers": {"user-agent": "API Client"}
        }
    
    def test_process_request_logs_no_redis(self):
        """Test handling when Redis is not configured."""
        # redis client is None because default settings not config it
        result = process_request_logs()
        self.assertEqual(result, {"error": "Redis client not configured"})
        
    @mock.patch('request_track.tasks.redis_client')
    def test_process_request_logs_empty(self, mock_redis_client):
        """Test handling when no logs to process."""
        mock_redis_client.__bool__.return_value = True
        mock_pipeline = mock.MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        # No items in Redis
        mock_pipeline.execute.return_value = ([], None)
        
        result = process_request_logs()
        
        self.assertIsNone(result)
        self.assertEqual(RequestLog.objects.count(), 0)
        
    @mock.patch('request_track.tasks.redis_client')
    @mock.patch('request_track.tasks.msgpack')
    def test_process_request_logs_with_ip_model(self, mock_msgpack, mock_redis_client):
        """Test processing logs with IP relation."""
        mock_redis_client.__bool__.return_value = True
        mock_pipeline = mock.MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        # Pack the log data
        packed_data_1 = msgpack.dumps(self.log_data_with_ip)
        
        # One item in Redis
        mock_pipeline.execute.return_value = ([packed_data_1], None)
        
        # Mock msgpack.loads to return our original data
        mock_msgpack.loads.return_value = self.log_data_with_ip
        
        # Check stats before
        self.assertEqual(RequestLog.objects.count(), 0)
        self.assertEqual(IpAddress.objects.count(), 0)
        
        result = process_request_logs()
        
        # Check results
        self.assertEqual(RequestLog.objects.count(), 1)
        self.assertEqual(IpAddress.objects.count(), 1)
        
        # Verify the IP address was created
        self.assertTrue(IpAddress.objects.filter(ip="192.168.1.1").exists())
        
        # Verify the log was created
        log = RequestLog.objects.first()
        self.assertEqual(log.ip.ip, "192.168.1.1")
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.route, "/test/")
        self.assertEqual(log.status_code, 200)
        
    @mock.patch('request_track.tasks.redis_client')
    @mock.patch('request_track.tasks.msgpack')
    def test_process_request_logs_with_direct_ip(self, mock_msgpack, mock_redis_client):
        """Test processing logs with direct IP address."""
        mock_redis_client.__bool__.return_value = True
        mock_pipeline = mock.MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        # Pack the log data
        packed_data_2 = msgpack.dumps(self.log_data_with_direct_ip)
        
        # One item in Redis
        mock_pipeline.execute.return_value = ([packed_data_2], None)
        
        # Mock msgpack.loads to return our original data
        mock_msgpack.loads.return_value = self.log_data_with_direct_ip
        
        # Check stats before
        self.assertEqual(RequestLog.objects.count(), 0)
        
        result = process_request_logs()
        
        # Check results
        self.assertEqual(RequestLog.objects.count(), 1)
        
        # Verify the log was created
        log = RequestLog.objects.first()
        self.assertIsNone(log.ip)
        self.assertEqual(log.ip_address, "192.168.1.2")
        self.assertIsNone(log.user)
        self.assertEqual(log.method, "POST")
        self.assertEqual(log.route, "/api/")
        self.assertEqual(log.status_code, 201)
        
    @mock.patch('request_track.tasks.redis_client')
    @mock.patch('request_track.tasks.msgpack')
    def test_process_request_logs_multiple(self, mock_msgpack, mock_redis_client):
        """Test processing multiple logs at once."""
        mock_redis_client.__bool__.return_value = True
        mock_pipeline = mock.MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        # Pack the log data
        packed_data_1 = msgpack.dumps(self.log_data_with_ip)
        packed_data_2 = msgpack.dumps(self.log_data_with_direct_ip)
        
        # Multiple items in Redis
        mock_pipeline.execute.return_value = ([packed_data_1, packed_data_2], None)
        
        # Mock msgpack.loads to return our original data
        mock_msgpack.loads.side_effect = [
            self.log_data_with_ip,
            self.log_data_with_direct_ip
        ]
        
        # Check stats before
        self.assertEqual(RequestLog.objects.count(), 0)
        self.assertEqual(IpAddress.objects.count(), 0)
        
        result = process_request_logs()
        
        # Check results
        self.assertEqual(RequestLog.objects.count(), 2)
        self.assertEqual(IpAddress.objects.count(), 1)
        
    @mock.patch('request_track.tasks.redis_client')
    @mock.patch('request_track.tasks.msgpack')
    def test_process_request_logs_max_items(self, mock_msgpack, mock_redis_client):
        """Test processing logs with max_items parameter."""
        mock_redis_client.__bool__.return_value = True
        mock_pipeline = mock.MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        # Pack the log data
        packed_data = msgpack.dumps(self.log_data_with_ip)
        
        # One item in Redis
        mock_pipeline.execute.return_value = ([packed_data], None)
        
        # Mock msgpack.loads to return our original data
        mock_msgpack.loads.return_value = self.log_data_with_ip
        
        # Process with max_items=10
        result = process_request_logs(max_items=10)
        
        # Should call spop with the limit
        mock_pipeline.spop.assert_called_with(mock.ANY, 10)
        
        # Check results
        self.assertEqual(RequestLog.objects.count(), 1)
        
    @mock.patch('request_track.tasks.redis_client')
    @mock.patch('request_track.tasks.msgpack')
    def test_process_request_logs_existing_ip(self, mock_msgpack, mock_redis_client):
        """Test processing logs when IP already exists in database."""
        # Create the IP address first
        ip = IpAddress.objects.create(ip="192.168.1.1")
        
        mock_redis_client.__bool__.return_value = True
        mock_pipeline = mock.MagicMock()
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        # Pack the log data
        packed_data = msgpack.dumps(self.log_data_with_ip)
        
        # One item in Redis
        mock_pipeline.execute.return_value = ([packed_data], None)
        
        # Mock msgpack.loads to return our original data
        mock_msgpack.loads.return_value = self.log_data_with_ip
        
        # Check stats before
        self.assertEqual(RequestLog.objects.count(), 0)
        self.assertEqual(IpAddress.objects.count(), 1)
        
        result = process_request_logs()
        
        # Check results - IP count should not change
        self.assertEqual(RequestLog.objects.count(), 1)
        self.assertEqual(IpAddress.objects.count(), 1)
        
        # Verify the log correctly references the existing IP
        log = RequestLog.objects.first()
        self.assertEqual(log.ip, ip)