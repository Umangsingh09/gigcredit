from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.credit import router as credit_router
from backend.app.api.worker import router as worker_router

app = FastAPI(
    title="GigCredit API",
    description="Alternative credit underwriting API for gig workers",
    version="1.0.0",
)

# Enable CORS for Flutter Web / Android / Desktop clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "GigCredit API Core Engine"
    }


app.include_router(auth_router)
app.include_router(credit_router)
app.include_router(worker_router)
