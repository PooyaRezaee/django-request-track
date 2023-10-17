# django-request-logger

## Overview
'django-request-logger' is a Django package designed to capture and store HTTP requests essential information, including IP address, user model, user agent, HTTP method, timestamp, and more.

## Installation
Install the package using pip:
```Shell
    pip install django-request-track
```

## Usage
1. Add request_track to your INSTALLED_APPS in your Django project's settings:
    ```python
        INSTALLED_APPS = [
        # ...
        'request_track',
        # ...
        ]
    ```

2. Register the middleware in your MIDDLEWARE settings:
    ```python
        MIDDLEWARE = [
            # ...
            'request_track.middleware.LoggingRequestMiddleware'
        ]
    ```

3. Migrate:
    ```Shell
        python manage.py migrate
    ```

After it all work will be done automatically and you can see the information through the Django admin panel or work with the "RequestLog" model.