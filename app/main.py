import os
import time
from app.rag import embedder
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader
import io
from app.rag import index_pdf, clear_collection
from app.llm import get_ai_reply, generate_quiz, generate_flashcards
from app.database import (
    init_db, save_message,
    init_documents_table, save_document, get_latest_document,
    clear_messages, clear_documents
)

app = FastAPI(title="StudyMate")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="templates"), name="assets")

init_db()
init_documents_table()

os.makedirs("./uploads", exist_ok=True)

class ChatMessage(BaseModel):
    message: str

class QuizRequest(BaseModel):
    question_count: int = Field(default=10, ge=3, le=15)

class FlashcardsRequest(BaseModel):
    card_count: int = Field(default=12, ge=3, le=30)

@app.get("/test-embed")
def test_embed():
    texts = ["This is a test sentence about machine learning."] * 8
    t0 = time.time()
    embeddings = list(embedder.embed(texts))
    elapsed = time.time() - t0
    return {"elapsed_seconds": elapsed}

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html", context={})

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    filename = os.path.basename((file.filename or "").replace("\\", "/"))
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Choose a PDF file to upload.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a readable PDF."
        ) from error

    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text was found in the PDF."
        )

    save_path = os.path.join("./uploads", filename)
    with open(save_path, "wb") as f:
        f.write(pdf_bytes)

    num_chunks = index_pdf(save_path, doc_id=filename)
    save_document(filename, extracted_text)

    return {"message": f"'{filename}' uploaded successfully.", "chunks": num_chunks}

@app.post("/chat")
def chat(chat_message: ChatMessage):
    latest_document = get_latest_document()
    active_doc_id = latest_document["filename"] if latest_document else None
    try:
        bot_reply = get_ai_reply(chat_message.message, doc_id=active_doc_id)
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail="AI providers could not answer. Check the API configuration and try again."
        ) from error
    save_message(chat_message.message, bot_reply)
    return {"reply": bot_reply}

@app.post("/quiz")
def create_quiz(quiz_request: QuizRequest):
    latest_document = get_latest_document()
    if not latest_document:
        raise HTTPException(status_code=404, detail="Upload a PDF before creating a quiz.")
    try:
        return generate_quiz(
            doc_id=latest_document["filename"],
            question_count=quiz_request.question_count
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail="AI providers could not generate a quiz. Check the API configuration and try again."
        ) from error

@app.post("/flashcards")
def create_flashcards(request: FlashcardsRequest):
    latest_document = get_latest_document()
    if not latest_document:
        raise HTTPException(status_code=404, detail="Upload a PDF before creating flashcards.")
    try:
        return generate_flashcards(
            doc_id=latest_document["filename"],
            card_count=request.card_count
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail="AI providers could not generate flashcards. Check the API configuration and try again."
        ) from error


@app.post("/clear")
def clear_chat():
    clear_messages()
    clear_documents()
    clear_collection()
    for filename in os.listdir("./uploads"):
        path = os.path.join("./uploads", filename)
        if os.path.isfile(path):
            os.remove(path)
    return {"message": "Chat history and uploaded documents cleared."}

