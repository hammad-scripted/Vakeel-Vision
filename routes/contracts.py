import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from database import contracts_collection
from  models.schemas import ContractResponse, ContractCreate, ContractStatus, Contract
from service.document_parser import extract_text  # Path to your extract_text helper

load_dotenv()

router = APIRouter(prefix="/contracts", tags=["contracts"])

ALLOWED_EXTENSIONS = set(
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_EXTENSIONS", ".pdf,.txt").split(",")
)
MAX_FILE_SIZE_MB = float(os.getenv("MAX_FILE_SIZE_MB", "10.0"))
if MAX_FILE_SIZE_MB < 0:
    raise ValueError("MAX_FILE_SIZE_MB must be non-negative")
MAX_FILE_SIZE_BYTES = int(MAX_FILE_SIZE_MB * 1024 * 1024)
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")


@router.post(
    "/upload",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    description="Upload a contract in PDF or TXT format for analysis",
)
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read at most one byte beyond the configured limit so oversized files
    # are rejected without loading the entire upload into memory.
    content = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum limit of {MAX_FILE_SIZE_MB} MB.",
        )

    size_mb = len(content) / (1024 * 1024)

    # Save physical file on disk
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    temp_filename = f"{os.urandom(8).hex()}{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, temp_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(content)

        # Extract text content
        extracted = extract_text(file_path)
        extracted_text = extracted.get("text", "")
        contract_doc = Contract(
            filename=temp_filename,
            original_filename=file.filename,
            text_content=extracted_text,
            page_count=extracted.get("page_count", 1),
            file_path=file_path,
            file_size_mb=round(size_mb, 2),
            word_count=len(extracted_text.split()),
            status=ContractStatus.UPLOADED,
        )

        # Convert the Pydantic object to a dictionary and save it to MongoDB.
        doc_dict = contract_doc.model_dump()
        contracts_collection.insert_one(doc_dict)
    except Exception as exc:
        try:
            os.remove(file_path)
        except OSError:
            pass

        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(exc)}",
        ) from exc

    return ContractResponse(**doc_dict)


@router.get(
    "/",
    response_model=List[ContractResponse],
    description="Retrieve all contracts uploaded to the system",
)
def get_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[ContractStatus] = None,
):
    query = {}
    if status_filter:
        query["status"] = status_filter.value

    cursor = contracts_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    return list(cursor)


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    description="Retrieve a specific contract by its unique ID",
)
def get_contract_by_id(contract_id: str):
    contract = contracts_collection.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID '{contract_id}' not found.",
        )
    return contract
