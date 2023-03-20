from .models import RequestLog
from .utils import get_object_ip

class LoggingRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        RequestLog.objects.create(
            ip=get_object_ip(request),
            user=request.user if request.user.is_authenticated else None,
            method=request.method,
            route=request.path,
            status_code=response.status_code,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            query_params=request.GET,
        )

        return response