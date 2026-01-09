from fastapi import FastAPI
from app.api.routes import health, memory, query

def register_routes(app: FastAPI):
    app.include_router(health.router, tags=["System"])
    app.include_router(memory.router, tags=["Memory"])
    app.include_router(query.router, tags=["Query"])
