from fastapi import FastAPI

app = FastAPI(
    title="Vakeel Contracts API",
    description="AI-Powered Contract Analyzer    for Vakeels",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
def root():
    return {
        "app": "Vakeel Contracts API",
        "description": "AI-Powered Contract Analyzer for Vakeels",
        "endpoints": {
            "POST /contracts/upload": "Upload a contract in the form of a PDF or TXT file",
            "GET  /contracts/ ": "Retrieve all contracts uploaded to the system in the form of a list",
            "GET  /contracts/{contract_id}": "Retrieve a specific contract by its ID",
            "GET /analysis/{analysis_id}": "Retrieve a specific analysis by its ID",
            "GET /analysis/contract/{contract_id}": "Retrieve all analysis for a specific contract",
        },
    }
