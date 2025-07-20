from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from rag_pipeline.rag_engine import query_rag
from fastapi.middleware.cors import CORSMiddleware
from app.db import SessionLocal, ChatHistory
import logging
import os

app = FastAPI()

# Add this CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOGGING SETUP ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "build.log")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode="a"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    question: str
    answer: str
    # Remove source_chunks from the response model
    # source_chunks: list[str]

@app.get("/")
def read_root():
    return {"message": "Bank of Maharashtra Loan Assistant API. Use POST /ask."}

def save_chat_to_db(question, answer):
    db = SessionLocal()
    chat = ChatHistory(question=question, answer=answer)
    db.add(chat)
    db.commit()
    db.close()

@app.post("/ask", response_model=AskResponse)
async def ask(request: Request):
    data = await request.json()
    question = data["query"]
    logger.info(f"Received question: {question}")
    answer = query_rag(question)  # Only get the answer, not source_chunks
    if not answer:
        logger.warning("Invalid or empty query received.")
        raise HTTPException(status_code=400, detail="Invalid or empty query.")
    save_chat_to_db(question, answer)
    logger.info(f"Response: {answer}")
    return AskResponse(
        question=question,
        answer=answer,
        # Do not include source_chunks
    ) 