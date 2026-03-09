"""
Celery定时任务
"""
from celery_app import celery_app
from app.db.session import async_session_maker
from app.ai.memory.manager import memory_manager
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.utils.logger import app_logger
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import asyncio


def run_async(coro):
    """运行异步函数的辅助函数"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.periodic.cleanup_expired_memories")
def cleanup_expired_memories():
    """清理过期记忆"""
    async def _cleanup():
        try:
            app_logger.info("开始清理过期记忆...")
            async with async_session_maker() as db:
                await memory_manager.cleanup_expired_memories(db)
            app_logger.info("✅ 过期记忆清理完成")
        except Exception as e:
            app_logger.error(f"❌ 清理过期记忆失败: {e}")
            raise
    
    return run_async(_cleanup())


@celery_app.task(name="app.tasks.periodic.send_task_reminders")
def send_task_reminders():
    """发送任务提醒"""
    async def _send_reminders():
        try:
            app_logger.info("开始发送任务提醒...")
            
            # 查找今天到期的任务
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)
            
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Task, User).join(User).filter(
                        and_(
                            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                            Task.due_date >= datetime.combine(today, datetime.min.time()),
                            Task.due_date < datetime.combine(tomorrow, datetime.min.time())
                        )
                    )
                )
                
                tasks_and_users = result.all()
                
                reminder_count = 0
                for task, user in tasks_and_users:
                    # 这里应该发送邮件或推送通知
                    # 目前只记录日志
                    app_logger.info(
                        f"任务提醒: 用户={user.username}, "
                        f"任务={task.title}, 截止={task.due_date}"
                    )
                    reminder_count += 1
                
                app_logger.info(f"✅ 任务提醒发送完成，共 {reminder_count} 条")
                return reminder_count
                
        except Exception as e:
            app_logger.error(f"❌ 发送任务提醒失败: {e}")
            raise
    
    return run_async(_send_reminders())


@celery_app.task(name="app.tasks.periodic.generate_weekly_reports")
def generate_weekly_reports():
    """生成周报"""
    async def _generate_reports():
        try:
            app_logger.info("开始生成周报...")
            
            async with async_session_maker() as db:
                # 获取所有活跃用户
                result = await db.execute(
                    select(User).filter(User.is_active == True)
                )
                users = result.scalars().all()
                
                from app.services.progress_service import progress_service
                
                report_count = 0
                for user in users:
                    # 生成周报
                    report = await progress_service.generate_weekly_report(
                        user_id=user.id,
                        db=db
                    )
                    
                    # 这里应该发送邮件或保存报告
                    # 目前只记录日志
                    app_logger.info(
                        f"周报生成: 用户={user.username}, "
                        f"学习时长={report['study_hours']}h, "
                        f"完成模块={len(report['completed_modules'])}"
                    )
                    report_count += 1
                
                app_logger.info(f"✅ 周报生成完成，共 {report_count} 份")
                return report_count
                
        except Exception as e:
            app_logger.error(f"❌ 生成周报失败: {e}")
            raise
    
    return run_async(_generate_reports())
