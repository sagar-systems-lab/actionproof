from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ActionProof API",
    version="0.1.0",
    description="Phase 1 runtime skeleton. Deterministic control starts in Phase 2.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "phase": "01-foundation",
        "runtime": "fixture-shell",
    }
