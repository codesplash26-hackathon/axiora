from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
import config

from backend.pool import init_pool, shutdown_pool
from backend.api_routes import router as api_router
from backend.privacy_middleware import PrivacySanitizationMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    shutdown_pool()

app = FastAPI(
    title="CardioRecourse API",
    description="Clinical Decision Support Engine with XGBoost, SHAP, and DiCE",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Allow frontend dev server to communicate without CORS blocks
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PrivacySanitizationMiddleware)

app.include_router(api_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "service": "CardioRecourse API",
        "sla_timeout_seconds": config.SLA_TIMEOUT_SECONDS,
    }
