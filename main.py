from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import close_db, init_db
from routes import contracts
from routes import analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB connection and indexes
    init_db()
    yield
    # Shutdown: Close DB client connection cleanly
    close_db()


app = FastAPI(
    title="Vakeel Contracts API",
    description="AI-Powered Contract Analyzer for Vakeels",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
# Routers
app.include_router(contracts.router)    
app.include_router(analysis.router)

@app.get("/")
def root():
    return {
        "app": "Vakeel Contracts API",
        "description": "AI-Powered Contract Analyzer for Vakeels",
        "endpoints": {
            "POST /contracts/upload": "Upload a contract in the form of a PDF or TXT file",
            "GET /contracts/": "Retrieve uploaded contracts",
            "GET /contracts/{contract_id}": "Retrieve a specific contract by its ID",
        },
    }
