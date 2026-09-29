import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from openai import OpenAIError
from pydantic import BaseModel, Field

from database import analysis_collection, contracts_collection
from service.document_parser import extract_text
from service.openai_analysis import ANALYSIS_QUESTION, analyze_contract as generate_analysis

load_dotenv()

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    question: str = Field(default="", max_length=4000)


def _citation_ready_text(contract: dict) -> str:
    """Return extracted text with real source page markers for citations."""
    text_content = (contract.get("text_content") or "").strip()
    file_path = contract.get("file_path")

    # Older uploads stored PDF pages as one joined string. Re-extract from the
    # original file when available so citations use actual PDF page numbers.
    if file_path and os.path.isfile(file_path):
        try:
            extracted = extract_text(file_path)
            pages = extracted.get("pages", [])
            page_context = "\n\n".join(
                f"[Page {page['page']}]\n{page['text']}"
                for page in pages
                if page.get("text", "").strip()
            )
            if page_context:
                return page_context
            extracted_text = extracted.get("text", "").strip()
            if extracted_text:
                text_content = extracted_text
        except Exception:
            # Only stored single-page text can be cited safely without re-extraction.
            pass

    if not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has no extractable text content.",
        )

    # Plain text uploads are treated as one source page. A multi-page PDF
    # without its original file cannot be safely assigned page citations.
    source_filename = (
        contract.get("original_filename")
        or file_path
        or contract.get("filename")
        or ""
    )
    is_plain_text = os.path.splitext(source_filename)[1].lower() == ".txt"
    if contract.get("page_count") == 1 or is_plain_text:
        return f"[Page 1]\n{text_content}"

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=(
            "Page boundaries are unavailable for this older PDF upload. "
            "Re-upload the PDF to generate page-accurate citations."
        ),
    )


@router.post("/analyze/{contract_id}", status_code=status.HTTP_201_CREATED)
def analyze_contract(contract_id: str, request: AnalysisRequest | None = None):
    if not contract_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract ID is required for analysis.",
        )

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured.",
        )

    contract = contracts_collection.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID '{contract_id}' not found.",
        )

    citation_ready_text = _citation_ready_text(contract)
    source_name = contract.get("original_filename") or contract.get("filename") or contract_id
    question = (request.question.strip() if request else "") or ANALYSIS_QUESTION

    contracts_collection.update_one(
        {"_id": contract["_id"]}, {"$set": {"status": "analyzing"}}
    )

    try:
        analysis_text = generate_analysis(
            document_name=source_name,
            text_content=citation_ready_text,
            question=question,
        )
        analyzed_at = datetime.now(timezone.utc)
        analysis_collection.update_one(
            {"contract_id": contract_id},
            {
                "$set": {
                    "contract_id": contract_id,
                    "document_name": source_name,
                    "question": question,
                    "analysis": analysis_text,
                    "model": "gpt-6-luna",
                    "analyzed_at": analyzed_at,
                }
            },
            upsert=True,
        )
        contracts_collection.update_one(
            {"_id": contract["_id"]}, {"$set": {"status": "analyzed"}}
        )
    except OpenAIError as exc:
        contracts_collection.update_one(
            {"_id": contract["_id"]}, {"$set": {"status": "error"}}
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI could not complete the contract analysis.",
        ) from exc
    except RuntimeError as exc:
        contracts_collection.update_one(
            {"_id": contract["_id"]}, {"$set": {"status": "error"}}
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI returned no analysis.",
        ) from exc
    except Exception as exc:
        contracts_collection.update_one(
            {"_id": contract["_id"]}, {"$set": {"status": "error"}}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The contract analysis failed.",
        ) from exc

    return {
        "contract_id": contract_id,
        "document_name": source_name,
        "question": question,
        "analysis": analysis_text,
        "analyzed_at": analyzed_at,
    }
