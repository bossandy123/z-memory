from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import register_routes
from app.database.models import init_db

app = FastAPI(title="Z-Memory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

register_routes(app)
