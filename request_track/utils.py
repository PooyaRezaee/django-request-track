from .models import IpAddress

def get_ip_address(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip

def get_or_create_object_ip(ip):
    if IpAddress.objects.filter(ip=ip).exists():
        return IpAddress.objects.get(ip=ip)
    else:
        return IpAddress.objects.create(ip=ip)
