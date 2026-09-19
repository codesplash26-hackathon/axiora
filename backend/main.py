from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api_routes import router
from backend.pool import get_executor, shutdown_executor, warmup_pool
from backend.worker import predict_worker

SAMPLE_WARMUP_PATIENT = {
    "male": 1,
    "age": 50,
    "currentSmoker": 0,
    "cigsPerDay": 0.0,
    "BPMeds": 0.0,
    "prevalentStroke": 0,
    "prevalentHyp": 0,
    "diabetes": 0,
    "totChol": 200.0,
    "sysBP": 120.0,
    "diaBP": 80.0,
    "BMI": 25.0,
    "heartRate": 70.0,
    "glucose": 80.0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize executor and pre-warm worker processes + model cache
    get_executor()
    try:
        await warmup_pool(predict_worker, SAMPLE_WARMUP_PATIENT)
    except Exception as e:
        print(f"Warning: Worker pre-warmup encountered an issue: {e}")
    yield
    # Shutdown: Cleanly terminate worker child processes
    shutdown_executor()


app = FastAPI(
    title="CardioRecourse API",
    description="Explainable & Actionable Clinical Decision Support System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
