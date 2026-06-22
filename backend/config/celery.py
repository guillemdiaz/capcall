import os
from celery import Celery

# Sets the default Django configuration module for Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("capcall")

# Reads all the Celery configuration from Django's settings.py
# (All variables starting with CELERY_ will be loaded)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically looks for asynchronous tasks in all tasks.py files
app.autodiscover_tasks()
