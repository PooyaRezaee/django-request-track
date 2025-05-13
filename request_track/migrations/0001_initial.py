from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IpAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(help_text='IPv4 or IPv6 address', unique=True, verbose_name='IP Address')),
            ],
            options={
                'verbose_name': 'IP Address',
                'verbose_name_plural': 'IP Addresses',
            },
        ),
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address stored directly (when IP model is disabled)', null=True, verbose_name='Direct IP Address')),
                ('user_agent', models.CharField(help_text='Browser or client information', max_length=300, verbose_name='User Agent')),
                ('route', models.CharField(db_index=True, help_text='URL path that was requested', max_length=1000, verbose_name='Route')),
                ('method', models.CharField(help_text='HTTP method (GET, POST, etc.)', max_length=10, verbose_name='Method')),
                ('query_params', models.TextField(help_text='URL query string parameters', verbose_name='Query Parameters')),
                ('status_code', models.PositiveIntegerField(db_index=True, help_text='HTTP response status code', verbose_name='Status Code')),
                ('requested_at', models.DateTimeField(db_index=True, help_text='Timestamp when the request was made', verbose_name='Requested At')),
                ('app_name', models.CharField(blank=True, db_index=True, help_text='Django application name if available', max_length=100, null=True, verbose_name='App Name')),
                ('headers', models.JSONField(blank=True, help_text='Selected HTTP headers from the request', null=True, verbose_name='Headers')),
                ('ip', models.ForeignKey(blank=True, help_text='Reference to IP address object', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='log', to='request_track.ipaddress', to_field='ip', verbose_name='IP Address')),
                ('user', models.ForeignKey(blank=True, help_text='User who made the request (if authenticated)', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Request Log',
                'verbose_name_plural': 'Request Logs',
                'ordering': ['-requested_at'],
                'indexes': [models.Index(fields=['requested_at', 'status_code'], name='request_tra_request_149612_idx'), models.Index(fields=['method', 'status_code'], name='request_tra_method_380349_idx')],
            },
        ),
    ]
