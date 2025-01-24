import re
import logging
from pdf2image import convert_from_path
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from app.utils.client_manager import client_manager
from app.config import settings

logger = logging.getLogger(__name__)

def _parse_llm_response(response_text: str) -> dict:
    """
    Parse the LLM's response looking for lines:

    Document Type: ...
    Tags: ...
    
    Returns a dict: { "document_type": "<type>", "tags": [ ... ] }
    """
    result = {
        "document_type": "unknown",
        "tags": []
    }

    # Extract Document Type: ...
    doc_type_match = re.search(r"(?i)document\s*type:\s*(.*)", response_text)
    if doc_type_match:
        possible_type = doc_type_match.group(1).strip()
        result["document_type"] = possible_type

    # Extract Tags: ...
    tags_match = re.search(r"(?i)tags:\s*(.*)", response_text)
    if tags_match:
        raw_tags = tags_match.group(1).strip()
        # Split by comma/newline
        split_tags = re.split(r"[,\n]+", raw_tags)
        result["tags"] = [tag.strip() for tag in split_tags if tag.strip()]

    return result


def _ocr_pdf(pdf_path: str) -> str:
    """
    Use OCR to extract text from a scanned PDF.
    Converts each page to an image and extracts text using pytesseract.
    """
    try:
        # Convert PDF to a list of images (one per page)
        pages = convert_from_path(pdf_path)

        # Extract text from each page using OCR
        ocr_text = ""
        for page in pages:
            ocr_text += pytesseract.image_to_string(page)

        return ocr_text
    except Exception as e:
        logger.error(f"OCR failed for PDF {pdf_path}: {e}")
        return ""


def process_pdf_document(pdf_path: str) -> dict:
    """
    1) Loads PDF content (with OCR if scanned).
    2) Calls Groq to generate a single document type (from a large list) + comma-separated tags.
    3) Returns {"document_type": "...", "tags": [...]}.
    """

    # -- 1) Try parsing the PDF normally --
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        all_content = "\n".join([d.page_content for d in docs if d.page_content])
    except Exception as e:
        logger.warning(f"Normal PDF parsing failed for {pdf_path}. Attempting OCR. Error: {e}")
        all_content = ""

    # -- 2) Fallback to OCR if parsing failed --
    if not all_content.strip():  # If no content was extracted
        logger.info(f"Attempting OCR for {pdf_path}")
        all_content = _ocr_pdf(pdf_path)

    if not all_content.strip():  # If OCR also fails
        logger.error(f"Failed to extract content from {pdf_path} via both parsing and OCR.")
        return {"document_type": "unknown", "tags": []}

    # -- 3) Prompt Setup --

    possible_doc_types = [
        "passport",
        "birth_certificate",
        "marriage_certificate",
        "death_certificate",
        "driver_license",
        "residence_permit",
        "visa",
        "national_ID_card",
        "social_security_card",
        "tax_statement",
        "utility_bill",
        "rental_agreement",
        "property_deed",
        "mortgage_statement",
        "employment_contract",
        "pay_slip",
        "health_insurance_card",
        "bank_statement",
        "credit_card_statement",
        "university_certificate",
        "school_transcript",
        "diploma",
        "official_form",
        "application_form",
        "registration_certificate",
        "notarial_act",
        "citizenship_certificate",
        "proof_of_address",
        "insurance_document",
        "medical_record",
        "vaccination_card",
        "police_clearance",
        "court_order",
        "power_of_attorney",
        "affidavit",
        "last_will_and_testament",
        "contract",
        "invoice",
        "purchase_receipt",
        "bill_of_sale",
        "customs_declaration",
        "shipping_document",
        "travel_itinerary",
        "boarding_pass",
        "train_ticket",
        "bus_ticket",
        "letter",
        "recommendation_letter",
        "reference_letter",
        "government_announcement",
        "academic_research_paper",
        "official_report",
        "minutes_of_meeting",
        "memorandum",
        "certified_translation",
        "bank_loan_agreement",
        "insurance_claim_form",
        "loan_approval_letter",
        "unknown"  # Always keep "unknown" as the fallback option
    ]

    system_prompt = (
        "You are a concise assistant that ONLY returns the document type and tags (no extra words).\n"
        "Pick exactly ONE document type from this list:\n"
        f"{', '.join(possible_doc_types)}\n"
        "If nothing fits, use 'unknown'.\n"
        "Then, provide a comma-separated list of tags summarizing its key topics.\n\n"
        "Format your response EXACTLY as:\n"
        "Document Type: <OneOfTheListAbove>\n"
        "Tags: <tag1>, <tag2>, <tag3>\n"
        "(No additional commentary.)"
    )

    user_prompt = (
        f"PDF Content:\n{all_content}\n\n"
        "Identify the single best document type from the list, and provide the main topics as comma-separated tags.\n"
        "Use the exact format requested."
    )

    try:
        client_manager.setup_clients()
        groq_client = client_manager.get_groq_client()

        response_stream = groq_client.chat.completions.create(
            model=settings.MODEL_NAME_CONVERSATIONAL_GROQ,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True,
            max_tokens=300,
            temperature=0.2,
        )

        response_text = ""
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                token = chunk.choices[0].delta.content
                if token:
                    response_text += token

        # -- 4) Parse LLM response into { document_type, tags } --
        result = _parse_llm_response(response_text)
        return result

    except Exception as e:
        logger.error(f"Error generating tags/document type with Groq: {e}")
        return {
            "document_type": "unknown",
            "tags": []
        }
