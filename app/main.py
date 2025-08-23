from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import router as v1_router

app = FastAPI(title=settings.PROJECT_NAME)

# CORS: permissive in dev, restrict via ALLOWED_ORIGINS in .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.ENV != "dev" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v1
app.include_router(v1_router, prefix=settings.API_V1_STR)
