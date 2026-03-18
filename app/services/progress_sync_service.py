"""
进度同步服务

负责学习路径与学习进度之间的同步和计算
"""
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.learning_path import LearningPath, PathModule, PathStatus
from app.models.progress import LearningProgress, ProgressStatus, ProgressHistory, ProgressTriggerType
from app.utils.logger import app_logger


class ProgressSyncService:
    """进度同步服务"""

    # 模块关键词映射（用于从对话中识别模块）
    MODULE_KEYWORDS = {
        "lecture_01": ["课程介绍", "概述", "学习方法"],
        "lecture_02": ["行业", "应用", "场景"],
        "lecture_03": ["prompt", "提示词", "基础prompt"],
        "lecture_04": ["中级prompt", "提示技巧"],
        "lecture_05": ["高级prompt", "chain of thought", "思维链"],
        "lecture_06": ["prompt实战", "prompt项目"],
        "lecture_07": ["prompt工程", "工程化"],
        "lecture_08": ["embedding", "嵌入", "向量"],
        "lecture_09": ["向量数据库", "milvus", "faiss"],
        "lecture_10": ["检索", "召回"],
        "lecture_11": ["rag基础", "检索增强"],
        "lecture_12": ["rag进阶", "高级rag"],
        "lecture_13": ["rag优化", "rag调优"],
        "lecture_14": ["rag系统", "rag实战"],
        "lecture_15": ["agent基础", "智能体基础"],
        "lecture_16": ["tool use", "工具调用"],
        "lecture_17": ["多agent", "multi-agent"],
        "lecture_18": ["agent框架", "langchain", "langgraph"],
        "lecture_19": ["agent实战", "agent项目"],
        "lecture_20": ["综合项目", "大作业"],
    }

    def generate_module_key(self, module_str: str) -> str:
        """
        从模块字符串生成标准化的模块key

        Args:
            module_str: 模块字符串，如 "讲03-07" 或 "讲14-RAG系统"

        Returns:
            标准化的模块key，如 "lecture_03_07" 或 "lecture_14"
        """
        # 提取数字
        numbers = re.findall(r'\d+', module_str)
        if not numbers:
            # 没有数字，使用哈希
            return f"module_{hash(module_str) % 10000}"

        if len(numbers) == 1:
            return f"lecture_{numbers[0].zfill(2)}"
        else:
            # 多个数字，如 "讲03-07" -> "lecture_03_07"
            return f"lecture_{'_'.join(n.zfill(2) for n in numbers)}"

    async def sync_path_modules(
        self,
        path: LearningPath,
        db: AsyncSession
    ) -> List[PathModule]:
        """
        同步学习路径的模块到 PathModule 表

        Args:
            path: 学习路径对象
            db: 数据库会话

        Returns:
            创建的 PathModule 列表
        """
        app_logger.info(f"开始同步路径模块: path_id={path.id}")

        # 1. 删除该路径现有的模块（级联删除会处理相关进度）
        await db.execute(
            delete(PathModule).where(PathModule.learning_path_id == path.id)
        )

        # 2. 解析 phases 并创建新模块
        created_modules = []
        phases = path.phases or []

        for phase_idx, phase in enumerate(phases):
            phase_title = phase.get("title", f"阶段{phase_idx + 1}")
            modules = phase.get("modules", [])

            for order_idx, module_str in enumerate(modules):
                # 处理模块字符串
                if isinstance(module_str, str):
                    module_key = self.generate_module_key(module_str)
                    module_name = module_str
                elif isinstance(module_str, dict):
                    module_key = module_str.get("key", self.generate_module_key(module_str.get("name", "")))
                    module_name = module_str.get("name", "未命名模块")
                else:
                    continue

                # 创建 PathModule
                path_module = PathModule(
                    learning_path_id=path.id,
                    phase_index=phase_idx,
                    phase_title=phase_title,
                    order_index=order_idx,
                    module_key=module_key,
                    module_name=module_name,
                    estimated_hours=2.0  # 默认2小时
                )
                db.add(path_module)
                created_modules.append(path_module)

        await db.flush()

        # 3. 为每个模块创建对应的 LearningProgress
        for module in created_modules:
            progress = LearningProgress(
                user_id=path.user_id,
                path_module_id=module.id,
                module_name=module.module_name,
                status=ProgressStatus.NOT_STARTED,
                completion_percentage=0.0,
                actual_hours=0.0
            )
            db.add(progress)

        await db.commit()

        app_logger.info(f"同步完成: 创建了 {len(created_modules)} 个模块")
        return created_modules

    async def get_path_progress(
        self,
        path_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取学习路径的详细进度

        Args:
            path_id: 路径ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            路径进度详情
        """
        # 获取路径
        result = await db.execute(
            select(LearningPath).filter(
                LearningPath.id == path_id,
                LearningPath.user_id == user_id
            )
        )
        path = result.scalar_one_or_none()
        if not path:
            return None

        # 获取所有模块及其进度
        result = await db.execute(
            select(PathModule, LearningProgress)
            .outerjoin(LearningProgress, PathModule.id == LearningProgress.path_module_id)
            .filter(PathModule.learning_path_id == path_id)
            .order_by(PathModule.phase_index, PathModule.order_index)
        )
        rows = result.all()

        # 按阶段组织数据
        phases_dict: Dict[int, Dict] = {}
        total_completion = 0.0
        total_hours = 0.0
        estimated_total = 0.0
        completed_count = 0
        current_module = None
        next_module = None

        for module, progress in rows:
            phase_idx = module.phase_index

            if phase_idx not in phases_dict:
                # 从原始 phases 获取阶段信息
                original_phase = path.phases[phase_idx] if phase_idx < len(path.phases) else {}
                phases_dict[phase_idx] = {
                    "phase_index": phase_idx,
                    "phase_title": module.phase_title or original_phase.get("title", f"阶段{phase_idx + 1}"),
                    "weeks": original_phase.get("weeks", ""),
                    "goal": original_phase.get("goal", ""),
                    "completion_percentage": 0.0,
                    "modules": [],
                    "completed_modules": 0,
                    "total_modules": 0,
                }

            # 模块进度详情
            module_detail = {
                "module_key": module.module_key,
                "module_name": module.module_name,
                "phase_index": phase_idx,
                "phase_title": module.phase_title,
                "completion_percentage": progress.completion_percentage if progress else 0.0,
                "actual_hours": progress.actual_hours if progress else 0.0,
                "estimated_hours": module.estimated_hours,
                "status": progress.status.value if progress else ProgressStatus.NOT_STARTED.value,
                "started_at": progress.started_at.isoformat() if progress and progress.started_at else None,
                "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
                "last_activity": progress.updated_at.isoformat() if progress else None,
            }

            phases_dict[phase_idx]["modules"].append(module_detail)
            phases_dict[phase_idx]["total_modules"] += 1

            # 统计
            completion = progress.completion_percentage if progress else 0.0
            total_completion += completion
            total_hours += progress.actual_hours if progress else 0.0
            estimated_total += module.estimated_hours

            if progress and progress.status == ProgressStatus.COMPLETED:
                phases_dict[phase_idx]["completed_modules"] += 1
                completed_count += 1
            elif progress and progress.status == ProgressStatus.IN_PROGRESS:
                if current_module is None:
                    current_module = module_detail
            elif not current_module and not next_module:
                if progress is None or progress.status == ProgressStatus.NOT_STARTED:
                    next_module = module_detail

        # 计算阶段完成度
        for phase in phases_dict.values():
            if phase["total_modules"] > 0:
                phase_total = sum(m["completion_percentage"] for m in phase["modules"])
                phase["completion_percentage"] = phase_total / phase["total_modules"]

        # 计算整体完成度
        total_modules = len(rows)
        overall_completion = total_completion / total_modules if total_modules > 0 else 0.0

        return {
            "path_id": path.id,
            "path_title": path.title,
            "overall_completion": round(overall_completion, 2),
            "status": path.status.value,
            "phases": list(phases_dict.values()),
            "total_study_hours": round(total_hours, 2),
            "estimated_total_hours": round(estimated_total, 2),
            "current_module": current_module,
            "next_module": next_module,
            "completed_modules_count": completed_count,
            "total_modules_count": total_modules,
        }

    async def update_module_progress(
        self,
        user_id: int,
        module_key: str,
        completion_delta: float,
        trigger_type: ProgressTriggerType,
        trigger_source: Optional[str] = None,
        trigger_detail: Optional[str] = None,
        db: AsyncSession = None
    ) -> Optional[LearningProgress]:
        """
        更新模块进度

        Args:
            user_id: 用户ID
            module_key: 模块标识
            completion_delta: 进度增量（正数增加，负数减少）
            trigger_type: 触发类型
            trigger_source: 触发来源
            trigger_detail: 触发详情
            db: 数据库会话

        Returns:
            更新后的进度对象
        """
        # 查找模块和进度
        result = await db.execute(
            select(PathModule, LearningProgress)
            .outerjoin(LearningProgress, PathModule.id == LearningProgress.path_module_id)
            .join(LearningPath, PathModule.learning_path_id == LearningPath.id)
            .filter(
                LearningPath.user_id == user_id,
                PathModule.module_key == module_key
            )
        )
        row = result.first()

        if not row:
            app_logger.warning(f"未找到模块: user_id={user_id}, module_key={module_key}")
            return None

        module, progress = row

        # 如果进度不存在，创建一个
        if not progress:
            progress = LearningProgress(
                user_id=user_id,
                path_module_id=module.id,
                module_name=module.module_name,
                status=ProgressStatus.NOT_STARTED,
                completion_percentage=0.0,
                actual_hours=0.0
            )
            db.add(progress)
            await db.flush()

        # 记录旧值
        old_percentage = progress.completion_percentage
        old_status = progress.status

        # 更新进度
        new_percentage = max(0, min(100, old_percentage + completion_delta))
        progress.completion_percentage = new_percentage

        # 更新状态
        if new_percentage >= 100:
            progress.status = ProgressStatus.COMPLETED
            if not progress.completed_at:
                progress.completed_at = datetime.utcnow()
        elif new_percentage > 0:
            progress.status = ProgressStatus.IN_PROGRESS
            if not progress.started_at:
                progress.started_at = datetime.utcnow()

        # 记录历史
        # 兼容数据库中使用小写枚举值（manual/time/task...）的场景
        trigger_type_value = (
            trigger_type.value
            if hasattr(trigger_type, "value")
            else str(trigger_type).lower()
        )
        history = ProgressHistory(
            progress_id=progress.id,
            old_percentage=old_percentage,
            new_percentage=new_percentage,
            old_status=old_status,
            new_status=progress.status,
            trigger_type=trigger_type_value,
            trigger_source=trigger_source,
            trigger_detail=trigger_detail
        )
        db.add(history)

        await db.commit()
        await db.refresh(progress)

        app_logger.info(
            f"更新进度: module={module_key}, {old_percentage}% -> {new_percentage}%, "
            f"trigger={trigger_type.value}"
        )

        return progress

    async def identify_module_from_content(
        self,
        content: str,
        user_id: int,
        db: AsyncSession
    ) -> Optional[Tuple[str, float]]:
        """
        从对话内容中识别学习模块

        Args:
            content: 对话内容
            user_id: 用户ID
            db: 数据库会话

        Returns:
            (module_key, confidence) 或 None
        """
        content_lower = content.lower()

        # 1. 关键词匹配
        best_match = None
        best_score = 0

        for module_key, keywords in self.MODULE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in content_lower)
            if score > best_score:
                best_score = score
                best_match = module_key

        if best_match and best_score >= 1:
            # 检查用户是否有这个模块的路径
            result = await db.execute(
                select(PathModule)
                .join(LearningPath, PathModule.learning_path_id == LearningPath.id)
                .filter(
                    LearningPath.user_id == user_id,
                    LearningPath.status == PathStatus.ACTIVE,
                    PathModule.module_key.like(f"{best_match}%")
                )
            )
            module = result.scalar_one_or_none()

            if module:
                confidence = min(1.0, best_score * 0.3)  # 每个关键词0.3分，最多1.0
                return (module.module_key, confidence)

        return None

    async def calculate_conversation_progress_delta(
        self,
        content: str,
        response: str
    ) -> float:
        """
        根据对话内容计算进度增量

        Args:
            content: 用户问题
            response: AI回答

        Returns:
            进度增量（0-15）
        """
        # 简单规则：
        # - 基础问题：+5%
        # - 深入问题（包含"为什么"、"如何"、"原理"）：+10%
        # - 实践问题（包含"代码"、"实现"、"项目"）：+15%

        content_lower = content.lower()

        if any(kw in content_lower for kw in ["代码", "实现", "项目", "实战", "练习"]):
            return 15.0
        elif any(kw in content_lower for kw in ["为什么", "原理", "如何", "怎么", "区别"]):
            return 10.0
        else:
            return 5.0

    async def get_progress_history(
        self,
        user_id: int,
        module_key: Optional[str] = None,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[Dict]:
        """
        获取进度变更历史

        Args:
            user_id: 用户ID
            module_key: 模块标识（可选）
            limit: 返回数量限制
            db: 数据库会话

        Returns:
            历史记录列表
        """
        query = (
            select(ProgressHistory, LearningProgress, PathModule)
            .join(LearningProgress, ProgressHistory.progress_id == LearningProgress.id)
            .outerjoin(PathModule, LearningProgress.path_module_id == PathModule.id)
            .filter(LearningProgress.user_id == user_id)
            .order_by(ProgressHistory.created_at.desc())
            .limit(limit)
        )

        if module_key:
            query = query.filter(PathModule.module_key == module_key)

        result = await db.execute(query)
        rows = result.all()

        history_list = []
        for history, progress, module in rows:
            history_list.append({
                "id": history.id,
                "module_name": progress.module_name,
                "module_key": module.module_key if module else None,
                "old_percentage": history.old_percentage,
                "new_percentage": history.new_percentage,
                "old_status": history.old_status.value if history.old_status else None,
                "new_status": history.new_status.value if history.new_status else None,
                "trigger_type": history.trigger_type.value,
                "trigger_source": history.trigger_source,
                "created_at": history.created_at.isoformat(),
            })

        return history_list


# 全局服务实例
progress_sync_service = ProgressSyncService()
