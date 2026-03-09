"""
Celery应用配置
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "ai_learning_coach",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.periodic", "app.tasks.async_tasks"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 每小时清理过期记忆
    "cleanup-expired-memories": {
        "task": "app.tasks.periodic.cleanup_expired_memories",
        "schedule": crontab(minute=0),  # 每小时执行
    },
    # 每天早上8点发送任务提醒
    "send-task-reminders": {
        "task": "app.tasks.periodic.send_task_reminders",
        "schedule": crontab(hour=8, minute=0),  # 每天8点
    },
    # 每周一凌晨生成周报
    "generate-weekly-reports": {
        "task": "app.tasks.periodic.generate_weekly_reports",
        "schedule": crontab(hour=2, minute=0, day_of_week=1),  # 每周一凌晨2点
    },
}

if __name__ == "__main__":
    celery_app.start()
