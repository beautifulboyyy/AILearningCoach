"""
用户画像相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.profile import (
    UserProfileResponse,
    UserProfileUpdate,
    ProfileGenerateRequest,
    ProfileGenerateResponse
)
from app.services.profile_service import profile_service
from app.utils.logger import app_logger

router = APIRouter()


@router.get("/", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户画像

    如果画像不存在，自动创建一个空画像
    """
    profile = await profile_service.get_profile(current_user.id, db)

    if not profile:
        # 自动创建空画像
        profile = await profile_service.create_profile(
            user_id=current_user.id,
            profile_data={
                "learning_goal": "systematic_learning",
                "technical_background": {
                    "education": "",
                    "major": "",
                    "work_experience": "",
                    "tech_stack": []
                },
                "learning_preference": {
                    "style": "project_driven"
                }
            },
            db=db
        )
        app_logger.info(f"为用户 {current_user.id} 自动创建画像")

    return profile


@router.put("/", response_model=UserProfileResponse)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户画像

    如果画像不存在，自动创建新画像
    """
    # 转换为字典，排除None值和前端兼容字段（已在验证器中转换）
    profile_data = profile_update.model_dump(
        exclude_none=True,
        exclude={'background', 'tech_stack', 'learning_style'}  # 排除已转换的前端字段
    )

    app_logger.info(f"更新画像数据: {profile_data}")

    profile = await profile_service.update_profile(
        user_id=current_user.id,
        profile_data=profile_data,
        db=db
    )

    if not profile:
        # 画像不存在，创建新画像
        profile = await profile_service.create_profile(
            user_id=current_user.id,
            profile_data=profile_data,
            db=db
        )
        app_logger.info(f"为用户 {current_user.id} 创建新画像")

    return profile


@router.post("/generate", response_model=ProfileGenerateResponse)
async def generate_profile(
    request: ProfileGenerateRequest = ProfileGenerateRequest(),  # 提供默认值
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    从对话中自动生成用户画像
    
    如果不提供conversation_text，将从用户最近的对话中提取
    
    请求体示例:
    ```json
    {
        "conversation_text": "我是一名软件工程师，想学习AI...",
        "limit": 10
    }
    ```
    
    或留空，自动从最近对话提取:
    ```json
    {}
    ```
    """
    try:
        # 如果未提供对话文本，从数据库获取最近的对话
        if not request or not request.conversation_text:
            from app.models.conversation import Conversation, Message
            
            result = await db.execute(
                select(Conversation)
                .filter(Conversation.user_id == current_user.id)
                .order_by(Conversation.created_at.desc())
                .limit(1)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="暂无对话记录，无法生成画像"
                )
            
            # 获取对话消息
            msg_result = await db.execute(
                select(Message)
                .filter(Message.conversation_id == conversation.id)
                .order_by(Message.created_at)
                .limit(request.limit if request else 10)
            )
            messages = msg_result.scalars().all()
            
            conversation_text = "\n".join([
                f"{'用户' if msg.role == 'user' else '助手'}: {msg.content}"
                for msg in messages
            ])
        else:
            conversation_text = request.conversation_text
        
        profile = await profile_service.generate_profile_from_conversation(
            conversation_text=conversation_text,
            user_id=current_user.id,
            db=db
        )
        
        return ProfileGenerateResponse(
            profile=profile,
            extracted_info={
                "name": profile.name,
                "occupation": profile.occupation,
                "learning_goal": profile.learning_goal
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"生成画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成画像失败: {str(e)}"
        )
