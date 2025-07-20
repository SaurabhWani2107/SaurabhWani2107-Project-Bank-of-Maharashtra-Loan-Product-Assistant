import os
import json
import numpy as np
import faiss
from dotenv import load_dotenv
import google.generativeai as genai
from app.db import log_query

# --- CONFIG ---
INDEX_PATH = "rag_pipeline/faiss_index/index.faiss"
DOCSTORE_PATH = "rag_pipeline/faiss_index/docstore.json"
EMBED_MODEL = "models/embedding-001"    

# --- SETUP ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=GOOGLE_API_KEY)

# --- LOAD INDEX AND METADATA ---
def load_faiss_and_metadata():
    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCSTORE_PATH):
        raise FileNotFoundError("FAISS index or docstore not found. Run chunk_and_embed.py first.")
    index = faiss.read_index(INDEX_PATH)
    with open(DOCSTORE_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks

# --- EMBED QUERY ---
def embed_query(query: str):
    response = genai.embed_content(
        model=EMBED_MODEL,
        content=query,
        task_type="retrieval_query"
    )
    return np.array(response["embedding"], dtype="float32").reshape(1, -1)

# --- MAIN RAG FUNCTION ---
def query_rag(user_question: str, top_k: int = 3):
    if not user_question.strip():
        return "Please enter a valid question.", []
    index, chunks = load_faiss_and_metadata()
    query_emb = embed_query(user_question)
    D, I = index.search(query_emb, top_k)
    retrieved_chunks = [chunks[i] for i in I[0]]
    context = "\n\n".join([c['chunk'] for c in retrieved_chunks])

    prompt = (
        "You are a helpful assistant for Bank of Maharashtra loan queries.\n"
        "Answer the following question using only the provided context. "
        "If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_question}\n"
        "Answer:"
    )

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    answer = response.text

    # --- Log the question and answer ---
    try:
        log_query(user_question, answer)
    except Exception as e:
        print(f"Failed to log query: {e}")

    # Return both answer and the raw chunks (for API)
    return answer, [c['chunk'] for c in retrieved_chunks]

# --- Example usage ---
if __name__ == "__main__":
    question = input("Ask a question: ")
    if not question.strip():
        print("Please enter a valid question.")
    else:
        answer = query_rag(question, top_k=3)
        print("\n--- Answer ---\n")
        print(answer) 