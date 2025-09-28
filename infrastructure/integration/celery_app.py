"""
Celery application for background tasks.
Infrastructure Layer - Integration Package
"""

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Create Celery instance
celery_app = Celery(
    'elearning',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=[
        'infrastructure.integration.tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'infrastructure.integration.tasks.send_email': {'queue': 'emails'},
        'infrastructure.integration.tasks.generate_recommendations': {'queue': 'ai'},
        'infrastructure.integration.tasks.process_analytics': {'queue': 'analytics'},
        'infrastructure.integration.tasks.cleanup_data': {'queue': 'maintenance'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'generate-daily-recommendations': {
            'task': 'infrastructure.integration.tasks.generate_daily_recommendations',
            'schedule': 86400.0,  # Every 24 hours
        },
        'process-daily-analytics': {
            'task': 'infrastructure.integration.tasks.process_daily_analytics',
            'schedule': 3600.0,  # Every hour
        },
        'cleanup-old-data': {
            'task': 'infrastructure.integration.tasks.cleanup_old_data',
            'schedule': 604800.0,  # Every week
        },
        'send-learning-reminders': {
            'task': 'infrastructure.integration.tasks.send_learning_reminders',
            'schedule': 43200.0,  # Every 12 hours
        },
    },
    beat_schedule_filename='celerybeat-schedule',
)

# Task discovery
celery_app.autodiscover_tasks()

if __name__ == '__main__':
    celery_app.start()

