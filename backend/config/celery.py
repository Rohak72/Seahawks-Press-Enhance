import os
from celery import Celery

# Ensures that the Celery worker process knows which Django project settings to load,
# essentially converting between namespaces.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# MacOS has a safety feature that can crash Celery's default 'fork' process model, especially
# with libraries like PyTorch. Setting this var to YES disables that safety check, allowing
# child processes to spawn correctly.
os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')

# Create an instance of the Celery app and load configs (via above).
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically look for a 'tasks.py' module from all Django apps.
app.autodiscover_tasks()
