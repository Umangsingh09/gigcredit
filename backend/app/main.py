from fastapi import FastAPI

from backend.app.api.auth import router as auth_router
from backend.app.api.credit import router as credit_router


app = FastAPI(
    title="gigcredit API",
    description="Alternative credit underwriting API for gig workers",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "gigcredit API"
    }


app.include_router(auth_router)
app.include_router(credit_router)