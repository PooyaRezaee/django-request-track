from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('sample')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule the flush task
# Or can set manual by user with celery beat in django admin panel
from datetime import timedelta

app.conf.beat_schedule = {
    'flush-request-logs-every-interval': {
        'task': 'request_track.tasks.process_request_logs',
        'schedule': timedelta(seconds=1),
    },
}