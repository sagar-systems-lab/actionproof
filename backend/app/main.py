from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import actions_router, retrieval_router, runtime_router

app = FastAPI(
    title="ActionProof API",
    version="0.5.0",
    description="Runtime API for the ActionProof prototype.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(actions_router)
app.include_router(retrieval_router)
app.include_router(runtime_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "runtime": "prototype",
    }
