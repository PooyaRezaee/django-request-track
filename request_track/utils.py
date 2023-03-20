from .models import IpAddress

def get_object_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    if IpAddress.objects.filter(ip=ip).exists():
        return IpAddress.objects.get(ip=ip)
    else:
        return IpAddress.objects.create(ip=ip)
