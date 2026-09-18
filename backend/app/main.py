import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import actions_router, benchmark_router, retrieval_router, runtime_router
from app.api.runtime import warm_closed_loop_runtime


def allowed_origins() -> list[str]:
    raw = os.getenv(
        "ACTIONPROOF_ALLOWED_ORIGINS",
        "http://localhost:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await warm_closed_loop_runtime()
    yield


app = FastAPI(
    title="ActionProof API",
    version="0.6.0",
    description="Runtime API for the ActionProof prototype.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(actions_router)
app.include_router(retrieval_router)
app.include_router(runtime_router)
app.include_router(benchmark_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "runtime": "prototype",
    }
