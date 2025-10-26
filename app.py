from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn

from src.routes.health_route import router as health_router
from src.routes.search_route import router as search_router
from src.routes.index_route import router as index_router
from src.utils.logger import setup_logger

load_dotenv()
setup_logger()


app = FastAPI(
    title="Search Agent API",
    description="AI-powered search agent",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(search_router)
app.include_router(health_router)
app.include_router(index_router)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
