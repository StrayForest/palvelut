import os
import time

from celery import Celery
from celery.signals import before_task_publish, task_failure, task_prerun

from palvelut.metrics import record_queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

app = Celery("palvelut")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@before_task_publish.connect
def _stamp_enqueued_at(headers=None, **kwargs):
    if headers is not None:
        headers["palvelut_enqueued_at"] = time.time()


@task_prerun.connect
def _record_queue_age(task=None, **kwargs):
    headers = getattr(getattr(task, "request", None), "headers", None) or {}
    enqueued_at = headers.get("palvelut_enqueued_at")
    if isinstance(enqueued_at, (int, float)):
        record_queue(age_seconds=max(0.0, time.time() - float(enqueued_at)))


@task_failure.connect
def _record_queue_failure(**kwargs):
    record_queue(failed=True)
