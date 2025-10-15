from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from celery.signals import after_setup_task_logger, after_setup_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    worker_redirect_stdouts=True,
    worker_redirect_stdouts_level='INFO',
)

@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        ))
        logger.addHandler(handler)

@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
