"""
学习进度追踪服务
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from app.models.progress import LearningProgress, ProgressStatus
from app.models.conversation import Message, MessageRole
from app.models.task import Task, TaskStatus
from app.utils.logger import app_logger


class ProgressService:
    """进度追踪服务"""
    
    async def update_progress(
        self,
        user_id: int,
        module_name: str,
        status: ProgressStatus,
        completion_percentage: float,
        db: AsyncSession
    ) -> LearningProgress:
        """
        更新学习进度
        
        Args:
            user_id: 用户ID
            module_name: 模块名称
            status: 状态
            completion_percentage: 完成百分比
            db: 数据库会话
        
        Returns:
            进度对象
        """
        # 查找是否存在
        result = await db.execute(
            select(LearningProgress).filter(
                and_(
                    LearningProgress.user_id == user_id,
                    LearningProgress.module_name == module_name
                )
            )
        )
        progress = result.scalar_one_or_none()
        
        if progress:
            # 更新现有进度
            progress.status = status
            progress.completion_percentage = completion_percentage
            
            if status == ProgressStatus.IN_PROGRESS and not progress.started_at:
                progress.started_at = datetime.utcnow()
            
            if status == ProgressStatus.COMPLETED and not progress.completed_at:
                progress.completed_at = datetime.utcnow()
        else:
            # 创建新进度
            progress = LearningProgress(
                user_id=user_id,
                module_name=module_name,
                status=status,
                completion_percentage=completion_percentage,
                started_at=datetime.utcnow() if status != ProgressStatus.NOT_STARTED else None
            )
            db.add(progress)
        
        await db.commit()
        await db.refresh(progress)
        
        app_logger.info(f"更新进度: user_id={user_id}, module={module_name}, completion={completion_percentage}%")
        return progress
    
    async def get_progress_stats(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取进度统计

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            统计信息
        """
        # 获取所有进度
        result = await db.execute(
            select(LearningProgress).filter(LearningProgress.user_id == user_id)
        )
        all_progress = result.scalars().all()

        # 统计
        total_modules = len(all_progress)
        completed = sum(1 for p in all_progress if p.status == ProgressStatus.COMPLETED)
        in_progress = sum(1 for p in all_progress if p.status == ProgressStatus.IN_PROGRESS)
        not_started = sum(1 for p in all_progress if p.status == ProgressStatus.NOT_STARTED)

        # 计算总体完成度
        overall_completion = 0.0
        if total_modules > 0:
            overall_completion = sum(p.completion_percentage for p in all_progress) / total_modules

        # 当前学习模块
        current_module = None
        for p in all_progress:
            if p.status == ProgressStatus.IN_PROGRESS:
                current_module = p.module_name
                break

        # 获取本周数据
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # 获取本周完成的任务数
        result = await db.execute(
            select(func.count(Task.id)).filter(
                and_(
                    Task.user_id == user_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.completed_at >= week_start
                )
            )
        )
        completed_tasks = result.scalar() or 0

        # 获取本周每天的对话数量（用于估算学习时长）
        daily_hours = await self._get_daily_study_hours(user_id, db, week_start)
        total_study_hours = sum(daily_hours.values())

        # 计算学习天数
        learning_days = len([h for h in daily_hours.values() if h > 0])

        # 计算平均每日时长
        average_daily_hours = total_study_hours / 7 if total_study_hours > 0 else 0

        # 获取上周数据用于对比
        last_week_start = week_start - timedelta(days=7)
        last_week_hours = await self._get_daily_study_hours(user_id, db, last_week_start, week_start)
        last_week_total = sum(last_week_hours.values())

        # 计算周环比变化
        week_change = 0.0
        if last_week_total > 0:
            week_change = ((total_study_hours - last_week_total) / last_week_total) * 100

        # 获取最近4周的进度趋势
        weekly_trend = await self._get_weekly_progress_trend(user_id, db)

        return {
            "total_modules": total_modules,
            "completed_modules": completed,
            "in_progress_modules": in_progress,
            "not_started_modules": not_started,
            "overall_completion": overall_completion,
            "current_module": current_module,
            # 新增字段
            "total_study_hours": total_study_hours,
            "completed_tasks": completed_tasks,
            "learning_days": learning_days,
            "average_daily_hours": average_daily_hours,
            "week_change_percent": week_change,
            "daily_hours": daily_hours,  # 本周每日学习时长
            "weekly_trend": weekly_trend  # 最近4周进度趋势
        }

    async def _get_daily_study_hours(
        self,
        user_id: int,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime = None
    ) -> Dict[str, float]:
        """
        获取指定日期范围内每天的学习时长

        Args:
            user_id: 用户ID
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期（默认为当前时间）

        Returns:
            每日学习时长字典 {"周一": 2.5, "周二": 3.0, ...}
        """
        if end_date is None:
            end_date = datetime.utcnow()

        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        daily_hours = {name: 0.0 for name in weekday_names}

        # 按天统计对话数量
        for i in range(7):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            if day_end > end_date:
                break

            # 统计该天的用户消息数量
            result = await db.execute(
                select(func.count(Message.id)).filter(
                    and_(
                        Message.user_id == user_id,
                        Message.role == MessageRole.USER,
                        Message.created_at >= day_start,
                        Message.created_at < day_end
                    )
                )
            )
            message_count = result.scalar() or 0

            # 估算学习时长（每条消息约0.5小时）
            weekday = day_start.weekday()
            daily_hours[weekday_names[weekday]] = round(message_count * 0.5, 1)

        return daily_hours

    async def _get_weekly_progress_trend(
        self,
        user_id: int,
        db: AsyncSession,
        weeks: int = 4
    ) -> List[Dict[str, Any]]:
        """
        获取最近几周的进度趋势

        Args:
            user_id: 用户ID
            db: 数据库会话
            weeks: 周数

        Returns:
            进度趋势列表
        """
        now = datetime.utcnow()
        trend = []

        for i in range(weeks - 1, -1, -1):
            week_end = now - timedelta(weeks=i)
            week_start = week_end - timedelta(days=7)

            # 获取该周的完成百分比
            result = await db.execute(
                select(func.avg(LearningProgress.completion_percentage)).filter(
                    and_(
                        LearningProgress.user_id == user_id,
                        LearningProgress.updated_at <= week_end
                    )
                )
            )
            avg_completion = result.scalar() or 0

            trend.append({
                "week": f"W{weeks - i}",
                "completion": round(avg_completion, 1)
            })

        return trend
    
    async def generate_weekly_report(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        生成周报
        
        Args:
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            周报数据
        """
        # 计算本周范围
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        # 获取本周完成的模块
        result = await db.execute(
            select(LearningProgress).filter(
                and_(
                    LearningProgress.user_id == user_id,
                    LearningProgress.completed_at >= week_start,
                    LearningProgress.completed_at < week_end
                )
            )
        )
        completed_modules = [p.module_name for p in result.scalars().all()]
        
        # 获取本周提问数量
        result = await db.execute(
            select(func.count(Message.id)).filter(
                and_(
                    Message.user_id == user_id,
                    Message.role == MessageRole.USER,
                    Message.created_at >= week_start,
                    Message.created_at < week_end
                )
            )
        )
        questions_asked = result.scalar() or 0
        
        # 获取本周完成的任务数
        result = await db.execute(
            select(func.count(Task.id)).filter(
                and_(
                    Task.user_id == user_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.completed_at >= week_start,
                    Task.completed_at < week_end
                )
            )
        )
        tasks_completed = result.scalar() or 0
        
        # 简化的学习时长估算（基于对话数量）
        study_hours = questions_asked * 0.5  # 假设每个问题平均30分钟
        
        return {
            "week_start": week_start,
            "week_end": week_end,
            "study_hours": study_hours,
            "completed_modules": completed_modules,
            "questions_asked": questions_asked,
            "tasks_completed": tasks_completed,
            "difficulty_points": [],  # 需要分析高频问题
            "suggestions": ["继续保持学习节奏", "多做实践练习"]
        }


# 全局服务实例
progress_service = ProgressService()
