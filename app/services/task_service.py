"""
任务管理服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from app.models.task import Task, TaskStatus, TaskPriority
from app.utils.logger import app_logger


class TaskService:
    """任务管理服务"""
    
    async def create_task(
        self,
        user_id: int,
        task_data: Dict[str, Any],
        db: AsyncSession
    ) -> Task:
        """
        创建任务
        
        Args:
            user_id: 用户ID
            task_data: 任务数据
            db: 数据库会话
        
        Returns:
            任务对象
        """
        # 处理带时区的 datetime 字段，转换为 UTC naive datetime
        if 'due_date' in task_data and task_data['due_date'] is not None:
            due_date = task_data['due_date']
            if isinstance(due_date, datetime) and due_date.tzinfo is not None:
                # 转换为 UTC 并移除时区信息
                task_data['due_date'] = due_date.replace(tzinfo=None)
        
        task = Task(user_id=user_id, **task_data)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        app_logger.info(f"创建任务: user_id={user_id}, task_id={task.id}")
        return task
    
    async def get_task(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            任务对象
        """
        result = await db.execute(
            select(Task).filter(
                and_(
                    Task.id == task_id,
                    Task.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_tasks(
        self,
        user_id: int,
        db: AsyncSession,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Task], int]:
        """
        获取任务列表
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            (任务列表, 总数)
        """
        query = select(Task).filter(Task.user_id == user_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 获取任务列表
        query = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return list(tasks), total
    
    async def update_task(
        self,
        task_id: int,
        user_id: int,
        update_data: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[Task]:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            update_data: 更新数据
            db: 数据库会话
        
        Returns:
            更新后的任务
        """
        task = await self.get_task(task_id, user_id, db)
        if not task:
            return None
        
        # 处理带时区的 datetime 字段
        if 'due_date' in update_data and update_data['due_date'] is not None:
            due_date = update_data['due_date']
            if isinstance(due_date, datetime) and due_date.tzinfo is not None:
                update_data['due_date'] = due_date.replace(tzinfo=None)
        
        for key, value in update_data.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)
        
        # 如果状态变为完成，记录完成时间
        if update_data.get("status") == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        app_logger.info(f"更新任务: task_id={task_id}")
        return task
    
    async def delete_task(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            是否成功
        """
        task = await self.get_task(task_id, user_id, db)
        if not task:
            return False
        
        await db.delete(task)
        await db.commit()
        
        app_logger.info(f"删除任务: task_id={task_id}")
        return True
    
    async def complete_task(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[Task]:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            完成的任务
        """
        return await self.update_task(
            task_id=task_id,
            user_id=user_id,
            update_data={
                "status": TaskStatus.COMPLETED,
                "completed_at": datetime.utcnow()
            },
            db=db
        )


# 全局服务实例
task_service = TaskService()
