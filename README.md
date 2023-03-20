# django-request-logger

### Install Package
```Shell
    pip install django-request-tracker
```

### Add App To Install Apps & Register MiddleWare
```python
    INSTALLED_APPS = [
    ...
    'request_track',
    ...
    ]

    MIDDLEWARE = [
        ...
        'request_track.middleware.LoggingRequestMiddleware'
        ...
    ]
```