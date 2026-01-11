from fastapi import FastAPI
from app.api.routes import health, memory, query, rl, logs

def register_routes(app: FastAPI):
    app.include_router(health.router, tags=["System"], prefix="/api")
    app.include_router(memory.router, tags=["Memory"], prefix="/api")
    app.include_router(query.router, tags=["Query"], prefix="/api")
    app.include_router(rl.router, tags=["RL Flywheel"], prefix="/api")
    app.include_router(logs.router, tags=["Logs"], prefix="/api")
