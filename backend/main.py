from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import config

# Import the router
from backend.api_routes import router

app = FastAPI(
    title="CardioRecourse API",
    description="Clinical Decision Support Engine with XGBoost, SHAP, and DiCE",
    version="1.0.0",
    default_response_class=ORJSONResponse,
)

# Allow frontend dev server and dashboard ports to communicate without CORS blocks
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

# Include the endpoints
app.include_router(router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "service": "CardioRecourse API",
        "sla_timeout_seconds": config.SLA_TIMEOUT_SECONDS,
    }