from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, submission, translation
from app.services.sqlite_service import init_sqlite_db

load_dotenv()
init_sqlite_db()

app = FastAPI(
    title="AI-Assisted Translation Prototype",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health_get():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return {"status": "ok"}

app.include_router(admin.router, prefix="/api")
app.include_router(submission.router, prefix="/api")
app.include_router(translation.router)
