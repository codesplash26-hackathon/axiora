import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
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
# Active HIPAA Safe Harbor & Sri Lanka PDPA edge de-identification
app.add_middleware(PrivacySanitizationMiddleware)


@app.middleware("http")
async def audit_correlation_and_timing_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    response = await call_next(request)

    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    return response


app.include_router(router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "service": "CardioRecourse API",
        "sla_timeout_seconds": config.SLA_TIMEOUT_SECONDS,
    }