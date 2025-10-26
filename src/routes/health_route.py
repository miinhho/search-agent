from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = Field(description="Health status")


@router.get("/health", tags=["Health"], response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")
