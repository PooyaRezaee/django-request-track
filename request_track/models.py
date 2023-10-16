from django.db import models
from django.contrib.auth import get_user_model

class IpAddress(models.Model):
    """
    Represents an IPv4 address requested over HTTP.

    Attributes:
        ip (str): The IPv4 address.
    """

    ip = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return str(self.ip)

class RequestLog(models.Model):
    """
    Stores information about client requests.

    Attributes:
        ip (IpAddress): The associated IP address.
        user (User): The user who made the request, can be null.
        user_agent (str): The user agent string.
        route (str): The requested route.
        method (str): The HTTP method used (e.g., GET, POST).
        query_params (str): The query parameters of the request.
        status_code (int): The HTTP status code of the response.
        requested_at (datetime): The timestamp when the request was made.
    """
    
    ip = models.ForeignKey(IpAddress,on_delete=models.CASCADE,related_name='log')
    user = models.ForeignKey(get_user_model(),on_delete=models.SET_NULL,blank=True,null=True,db_index=True)
    user_agent = models.CharField(max_length=300)
    route = models.CharField(max_length=1000,db_index=True)
    method = models.CharField(max_length=10)
    query_params = models.TextField()
    status_code = models.PositiveIntegerField(db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True,db_index=True)

    class Meta:
        verbose_name = "Requests Log"

    def __str__(self):
        return f"{self.ip} - {self.user} - {self.route} - {self.status_code} - {self.requested_at}"
