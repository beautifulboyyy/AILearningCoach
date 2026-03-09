from fastapi import APIRouter, Depends
from app.services.plan_service import plan_service
from app.schemas.plan import PlanCreateRequest

router = APIRouter()

@router.post("/generate")
async def generate_plan(request: PlanCreateRequest):
    plan_data = await plan_service.generate_plan(
        user_background=request.background,
        target=request.target
    )
    # In a real app, you would save this to the database here
    return plan_data
