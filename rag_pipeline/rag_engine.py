import os
import json
import numpy as np
import faiss
from dotenv import load_dotenv
import google.generativeai as genai
from app.db import log_query
import logging
from typing import List, Tuple, Any

# --- CONFIG ---
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "rag_pipeline/faiss_index/index.faiss")
DOCSTORE_PATH = os.getenv("DOCSTORE_PATH", "rag_pipeline/faiss_index/docstore.json")
EMBED_MODEL = os.getenv("EMBED_MODEL", "models/embedding-001")
GEN_MODEL = os.getenv("GEN_MODEL", "models/gemini-2.5-flash")
TOP_K_DEFAULT = int(os.getenv("TOP_K_DEFAULT", 3))

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

# --- SETUP ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.critical("GOOGLE_API_KEY not found in .env file.")
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=GOOGLE_API_KEY)

# --- LOAD INDEX AND METADATA ---
def load_faiss_and_metadata() -> Tuple[faiss.Index, List[dict]]:
    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCSTORE_PATH):
        logger.error("FAISS index or docstore not found. Run chunk_and_embed.py first.")
        raise FileNotFoundError("FAISS index or docstore not found. Run chunk_and_embed.py first.")
    try:
        index = faiss.read_index(INDEX_PATH)
        with open(DOCSTORE_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        return index, chunks
    except Exception as e:
        logger.exception("Failed to load FAISS index or docstore.")
        raise

# --- EMBED QUERY ---
def embed_query(query: str) -> np.ndarray:
    try:
        response = genai.embed_content(
            model=EMBED_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        return np.array(response["embedding"], dtype="float32").reshape(1, -1)
    except Exception as e:
        logger.exception("Embedding failed.")
        raise RuntimeError("Failed to embed query.") from e

def format_answer_user_friendly(answer: str) -> str:
    """
    Formats the answer to be more user-friendly.
    - If the answer is long, splits it into bullet points.
    - Ensures a conversational tone.
    """
    import re

    answer = answer.strip()
    if len(answer) < 200 and answer.count('.') < 3:
        return answer

    if '\n' in answer:
        lines = [line.strip() for line in answer.split('\n') if line.strip()]
    else:
        lines = re.split(r'(?<=[.!?])\s+', answer)
        lines = [line.strip() for line in lines if line.strip()]

    if len(lines) <= 1:
        return answer

    formatted = "Here are the key points:\n"
    for line in lines:
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        formatted += f"• {line}\n"
    return formatted.strip()

def sanitize_user_input(user_input: str) -> str:
    # Add more sanitization as needed
    return user_input.strip()

def is_greeting(user_input: str) -> bool:
    greetings = [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "greetings", "namaste", "hola", "bonjour", "hii"
    ]
    user_input_lower = user_input.lower().strip()
    # Check if the input is exactly a greeting or starts with a greeting
    return any(
        user_input_lower == g or user_input_lower.startswith(g + " ") for g in greetings
    )

# --- MAIN RAG FUNCTION ---
def query_rag(user_question: str, top_k: int = TOP_K_DEFAULT, return_chunks: bool = False):
    user_question = sanitize_user_input(user_question)
    logger.info(f"RAG received question: {user_question}")
    if not user_question:
        logger.warning("Empty user question received.")
        return ("Please enter a valid question.", []) if return_chunks else "Please enter a valid question."

    # --- Handle greetings ---
    if is_greeting(user_question):
        greeting_response = "Hello! How can I assist you with your Bank of Maharashtra loan queries today?"
        logger.info(f"Greeting detected. Responding: {greeting_response}")
        return (greeting_response, []) if return_chunks else greeting_response

    try:
        index, chunks = load_faiss_and_metadata()
    except Exception as e:
        logger.error("System error: Unable to load knowledge base.")
        return ("System error: Unable to load knowledge base.", []) if return_chunks else "System error: Unable to load knowledge base."

    try:
        query_emb = embed_query(user_question)
    except Exception as e:
        logger.error("System error: Unable to process your question.")
        return ("System error: Unable to process your question.", []) if return_chunks else "System error: Unable to process your question."

    try:
        D, I = index.search(query_emb, top_k)
        retrieved_chunks = [chunks[i] for i in I[0] if i < len(chunks)]
        context = "\n\n".join([c['chunk'] for c in retrieved_chunks])
    except Exception as e:
        logger.exception("Retrieval failed.")
        return ("System error: Unable to retrieve relevant information.", []) if return_chunks else "System error: Unable to retrieve relevant information."

    if not context.strip():
        logger.info("No relevant context found for the question.")
        return ("Sorry, I couldn't find relevant information for your question.", []) if return_chunks else "Sorry, I couldn't find relevant information for your question."

    prompt = (
        "You are a helpful assistant for Bank of Maharashtra loan queries.\n"
        "Answer the following question using only the provided context. "
        "If the answer is long, present it in a pointwise or bullet format for clarity. "
        "If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_question}\n"
        "Answer:"
    )

    try:
        model = genai.GenerativeModel(GEN_MODEL)
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        logger.exception("Generative model failed.")
        return ("System error: Unable to generate an answer at this time.", []) if return_chunks else "System error: Unable to generate an answer at this time."

    answer = format_answer_user_friendly(answer)
    logger.info(f"RAG response: {answer}")

    try:
        log_query(user_question, answer)
    except Exception as e:
        logger.warning(f"Failed to log query: {e}")

    if return_chunks:
        return answer, [c['chunk'] for c in retrieved_chunks]
    else:
        return answer

# --- Example usage ---
if __name__ == "__main__":
    try:
        question = input("Ask a question: ")
        if not question.strip():
            print("Please enter a valid question.")
        else:
            answer, _ = query_rag(question, top_k=TOP_K_DEFAULT)
            print("\n--- Answer ---\n")
            print(answer)
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        logger.exception("Fatal error in main execution.") 