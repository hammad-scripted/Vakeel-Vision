import os
import uuid

from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile

load_dotenv()
router = APIRouter("/contracts", tags=["contracts"])


@router.get(
    "/",
    description="Retrieve all contracts uploaded to the system in the form of a list",
)
def get_contracts():
    pass


@router.post(
    "/upload", description="Upload a contract in the form of a PDF or TXT file"
)
async def upload_contract(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in os.getenv("ALLOWED_EXTENSIONS"):
        raise HTTPException(status_code=400, detail="Invalid file extension")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > os.getenv("MAX_FILE_SIZE"):
        raise HTTPException(status_code=400, detail="File size is too large")
    os.makedirs(os.getenv("UPLOAD_FOLDER"), exist_ok=True)
    file_path = os.path.join(os.getenv("UPLOAD_FOLDER"), f"{uuid.uuid4()}{ext}")

    with open(file_path, "wb") as f:
        f.write(content)
