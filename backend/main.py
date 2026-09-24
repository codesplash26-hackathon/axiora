from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config

from backend.api_routes import router
from backend.pool import init_pool, shutdown_pool
from backend.privacy_middleware import PrivacySanitizationMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-initialize process pool workers with ML pre-warming
    init_pool()
    yield
    # Shutdown: Gracefully stop all child processes
    shutdown_pool()


app = FastAPI(
    title="CardioRecourse API",
    description="Clinical Decision Support Engine with XGBoost, SHAP, and DiCE",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PrivacySanitizationMiddleware)

app.include_router(router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "service": "CardioRecourse API",
        "sla_timeout_seconds": config.SLA_TIMEOUT_SECONDS,
    }
