# django-request-track
![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![PyPi](https://img.shields.io/badge/pypi-3775A9?style=for-the-badge&logo=pypi&logoColor=white)

## Overview
'django-request-track' is a powerful Django package designed to capture and store HTTP requests essential information, including IP address, user model, user agent, HTTP method, timestamp, and more. It supports both synchronous and asynchronous operations, providing flexible logging options with Redis buffer and Celery integration for efficient request tracking.

## Features
- Track HTTP requests with detailed information
- Support for both sync and async operations
- Redis buffer with Celery integration for efficient logging
- Customizable request sampling
- Flexible user logging modes
- IP address tracking with optional separate model
- Customizable header logging
- Support for Django 5.0+

## Installation
Install the package using pip:
```bash
pip install django-request-track
```

## Quick Start
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

3. Run migrations:
    ```bash
    python manage.py migrate
    ```

## Configuration
You can customize the behavior of django-request-track through your Django settings:

```python
REQUEST_TRACK_SETTINGS = {
    # Specify which HTTP headers to log
    "HEADERS_TO_LOG": ["sec-ch-ua-platform"],
    
    # Paths that should always be logged (ignoring sampling)
    "FORCE_PATHS": ["/admin", "/critical-action"],
    
    # Paths to exclude from logging
    "EXCLUDE_PATHS": ["/admin/jsi18n/"],
    
    # User logging mode: 'all', 'authenticated', or 'anonymous'
    "USER_LOGGING_MODE": "all",
    
    # Sampling rate (0: no logging, 1: log all, 0.5: log 50% randomly)
    "SAMPLING_RATE": 1,
    
    # Whether FORCE_PATHS should respect sampling rate
    "FORCE_PATHS_SAMPLING": False,
    
    # Store IP addresses in a separate model
    "USE_IP_ADDRESS_MODEL": True,
    
    # Use Redis as a buffer for logging (recommended for production)
    "USE_REDIS_BUFFER": False,
    
    # Redis key for storing logs (required if USE_REDIS_BUFFER is True)
    "REDIS_KEY": "req_logs",
    
    # Redis connection URL (required if USE_REDIS_BUFFER is True)
    "REDIS_URL": "redis://localhost:6379/2",
}
```

## Usage Examples

### Basic Usage
The package will automatically start tracking requests once installed and configured. You can access the logs through:

1. Django Admin Interface (with built-in filtering and search)
2. RequestLog model:
```python
from request_track.models import RequestLog

# Get all logs
logs = RequestLog.objects.all()

# Get logs for a specific user
user_logs = RequestLog.objects.filter(user=user)

# Get logs for a specific IP
ip_logs = RequestLog.objects.filter(ip_address='192.168.1.1')
```

### Using Redis Buffer with Celery
For production environments, it's recommended to use Redis as a buffer with Celery for batch processing:

```python
REQUEST_TRACK_SETTINGS = {
    "USE_REDIS_BUFFER": True,
    "REDIS_KEY": "req_logs",
    "REDIS_URL": "redis://localhost:6379/2",
}
```

This configuration will:
1. Store logs in Redis temporarily
2. Process logs in batches using Celery
3. Reduce database load
4. Improve application performance

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Author
- PooyaRezaee (pooya.rezaee.official@gmail.com)

## Support
If you encounter any issues or have questions, please open an issue on GitHub.