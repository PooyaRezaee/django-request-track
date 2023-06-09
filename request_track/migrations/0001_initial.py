# Generated by Django 4.1.7 on 2023-03-20 15:15

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
                ('ip', models.GenericIPAddressField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_agent', models.CharField(max_length=300)),
                ('route', models.CharField(db_index=True, max_length=1000)),
                ('method', models.CharField(max_length=10)),
                ('query_params', models.TextField()),
                ('status_code', models.PositiveIntegerField(db_index=True)),
                ('requested_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('ip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log', to='request_track.ipaddress')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Requests Log',
            },
        ),
    ]
