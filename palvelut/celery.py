import os
import time

from celery import Celery, signals

from palvelut.observability import (
    capture_exception,
    observe_queue_age,
    observe_queue_failure,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

app = Celery("palvelut")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@signals.before_task_publish.connect
def _stamp_publish_time(headers=None, **kwargs):
    if headers is not None:
        headers["palvelut_published_at"] = time.time()


@signals.task_prerun.connect
def _observe_task_age(task=None, **kwargs):
    published_at = None
    if task is not None:
        published_at = (getattr(task.request, "headers", None) or {}).get(
            "palvelut_published_at"
        )
    if isinstance(published_at, (int, float)):
        observe_queue_age(time.time() - published_at)


@signals.task_failure.connect
def _observe_task_failure(exception=None, **kwargs):
    observe_queue_failure()
    if isinstance(exception, BaseException):
        capture_exception(exception)
