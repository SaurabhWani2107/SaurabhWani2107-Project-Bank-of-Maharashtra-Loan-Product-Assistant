from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from rag_pipeline.rag_engine import query_rag
from fastapi.middleware.cors import CORSMiddleware
from app.db import SessionLocal, ChatHistory

app = FastAPI()

# Add this CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    question: str
    answer: str
    source_chunks: list[str]

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
    answer, source_chunks = query_rag(question)
    if not answer or not source_chunks:
        raise HTTPException(status_code=400, detail="Invalid or empty query.")
    save_chat_to_db(question, answer)
    return AskResponse(
        question=question,
        answer=answer,
        source_chunks=source_chunks
    ) 