from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/")
async def serve_client():
    return FileResponse("static/index.html")
