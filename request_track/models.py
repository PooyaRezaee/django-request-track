from django.db import models
from django.contrib.auth import get_user_model

class IpAddress(models.Model):
    ip = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return str(self.ip)

class RequestLog(models.Model):
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
