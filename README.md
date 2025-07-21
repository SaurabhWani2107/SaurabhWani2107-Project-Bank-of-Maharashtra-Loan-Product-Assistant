# Bank of Maharashtra Loan Assistant (RAG-based Chatbot)

A full-stack Retrieval-Augmented Generation (RAG) application for answering Bank of Maharashtra loan queries using LLMs, web-scraped data, and a modern web frontend.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Folder & File Details](#folder--file-details)
- [Features](#features)
- [Project Evaluation Details](#project-evaluation-details)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Commands](#commands)
- [Development & Logs](#development--logs)
- [Contributing](#contributing)

---

## Project Structure

```
BOM/
├── app/                      # FastAPI backend & DB models
│   ├── main.py
│   └── db.py
├── rag_pipeline/             # RAG engine, chunking, embedding, FAISS index
│   ├── chunk_and_embed.py
│   ├── rag_engine.py
│   └── faiss_index/
├── webscrapping_scripts/     # Playwright-based web scrapers for loan data
│   ├── script_1.py ... script_16_ROI.py
├── Extracteddata_scriptwise/ # Scraped, structured text data (input to RAG)
│   ├── script_1.txt ... script_16_ROI.txt
├── frontend/                 # Next.js frontend
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── ...
├── logs/                     # Logs for backend, RAG, chunking
│   └── build.log
├── requirements.txt          # Python dependencies
└── README.md                 # (This file)
```

---

## Folder & File Details

### `/app/` — **Backend API & Database**
- **main.py**  
  FastAPI app exposing endpoints:
  - `GET /` — Health check/info.
  - `POST /ask` — Accepts a question, queries the RAG engine, saves Q&A to the database, and returns the answer.
  - Handles CORS for frontend, logging, and chat history storage.
- **db.py**  
  SQLAlchemy ORM models and DB connection:
  - `ChatHistory` and `QueryLog` tables for storing user queries and responses.
  - Auto-creates tables if not present.
  - Utility to log queries.

---

### `/rag_pipeline/` — **RAG Engine, Chunking, Embedding**
- **chunk_and_embed.py**  
  - Loads all `.txt` files from `Extracteddata_scriptwise/`.
  - Splits text into overlapping chunks.
  - Embeds each chunk using Google Gemini API.
  - Stores embeddings in a FAISS index (`faiss_index/index.faiss`) and metadata in `faiss_index/docstore.json`.
  - **Run:** `python rag_pipeline/chunk_and_embed.py`
- **rag_engine.py**  
  - Loads FAISS index and metadata.
  - Embeds user queries, retrieves top-k relevant chunks, constructs a prompt, and queries Gemini LLM.
  - Formats and returns the answer, logs Q&A to the database.
  - **Used by:** Backend API (`/app/main.py`).
  - **Run (CLI test):** `python rag_pipeline/rag_engine.py`
- **faiss_index/**  
  - `index.faiss`: Vector index for fast similarity search.
  - `docstore.json`: Metadata for each chunk (source, chunk id, etc.).

---

### `/webscrapping_scripts/` — **Automated Data Extraction**
- **script_1.py ... script_16_ROI.py**  
  - Each script targets a specific Bank of Maharashtra loan product or information page.
  - Uses Playwright to extract structured data: introductions, interest rates, features, eligibility, FAQs, etc.
  - Outputs are saved as `.txt` files in `Extracteddata_scriptwise/`.
  - **Run:** `python webscrapping_scripts/script_X.py` (replace `X` with the script number).

---

### `/Extracteddata_scriptwise/` — **Knowledge Base (Text)**
- **script_1.txt ... script_16_ROI.txt**  
  - Output of each webscraping script.
  - Contains structured, sectioned text for each loan product.
  - Used as input for chunking and embedding.

---

### `/frontend/` — **User Interface (Next.js)**
- **app/**  
  - Main React components and pages.
  - `chat/page.tsx`: Chat UI for interacting with the assistant.
  - `layout.tsx`, `globals.css`: Layout and global styles.
- **public/**  
  - Static assets (SVGs, icons).
- **package.json**  
  - Node.js dependencies and scripts.
- **tsconfig.json**  
  - TypeScript configuration.
- **next.config.ts**  
  - Next.js configuration.
- **Run:**  
    - `npm install` (install dependencies)  
    - `npm run dev` (start development server)

---

### `/logs/` — **Centralized Logging**
- **build.log**  
  - Logs from backend, RAG pipeline, and chunking/embedding processes.
  - Useful for debugging and monitoring.

---

### `/requirements.txt` — **Python Dependencies**
- All backend, RAG, and scraping dependencies are listed here.
- Install with: `pip install -r requirements.txt`

---

## Features

- **RAG Chatbot:** Answers user queries using LLMs and a custom knowledge base.
- **Web Scraping:** Automated scripts extract up-to-date loan information.
- **Chunking & Embedding:** Text is split and embedded for efficient retrieval.
- **FAISS Index:** Fast vector search for relevant context.
- **PostgreSQL Database:** Stores chat history and query logs.
- **Modern Frontend:** Next.js React app for user interaction.
- **Logging:** Centralized logs for all backend and pipeline operations.

---

### Project Setup

See the [Setup & Installation](#setup--installation) section below for step-by-step instructions on setting up the backend, frontend, and data pipeline. The process includes installing Python and Node.js dependencies, configuring environment variables, running web scrapers, chunking and embedding data, and starting both backend and frontend servers.

---

### Architectural Decisions

#### Libraries

- **Web Scraping:**  
  We chose **Playwright** for scraping because it handles dynamic, JavaScript-heavy government websites more robustly than alternatives like BeautifulSoup or Selenium. Playwright’s headless browser automation allows us to interact with complex page elements and extract structured data even from sites with heavy client-side rendering.
- **Data Processing:**  
  Standard Python libraries (e.g., `pandas`, `re`, `json`) are used for cleaning and structuring the scraped data. This ensures flexibility and easy integration with the rest of the pipeline.
- **RAG Pipeline:**  
  - **FAISS** is used for fast vector similarity search, enabling efficient retrieval of relevant knowledge chunks.
  - **Google Gemini API** is used for both embedding and LLM inference, providing state-of-the-art language understanding and generation.

#### Data Strategy

- **Chunking Approach:**  
  Text data from each scraped `.txt` file is split into overlapping chunks of a fixed size (e.g., 500 tokens with 100-token overlap). This strategy ensures that each chunk contains enough context for meaningful retrieval, while the overlap prevents information loss at chunk boundaries. The chunk size was chosen to balance retrieval granularity and LLM context window limitations.

#### Model Selection

- **Embedding Model:**  
  We use `embedding-001` from Google Gemini. This model was selected for its strong performance on semantic similarity tasks, multilingual support, and seamless integration with the Gemini LLM.
- **LLM:**  
  The main language model is Google Gemini 2.5 flash, chosen for its accuracy, speed, and ability to handle retrieval-augmented prompts effectively and also it is open source.

#### AI Tools Used

- **Cursor:** Used for code navigation, refactoring, and rapid prototyping.
- **NotebookLM:** Assisted in requirement understanding.
- **ChatGPT:** Used for brainstorming, code review, and documentation drafting.

---

### Challenges Faced

Scraping data from government websites proved tricky and difficult due to:
- Highly dynamic pages with frequent redirects and JavaScript-rendered content.
- Non-structured, inconsistent data formats across different loan product pages.
- Navigating through multiple layers of links and handling session/cookie requirements.
- Occasional anti-bot measures and rate limiting.

**Solutions:**  
We leveraged Playwright’s robust automation to simulate real user interactions, implemented retry logic for failed requests, and developed custom parsers to handle messy or irregular data layouts.

---

### Potential Improvements

- **Intent Handling:**  
  Integrate an agentic framework to recognize user intent and dynamically decide whether to fetch responses from the RAG pipeline, answer general queries, or perform live web lookups.
- **Frontend Enhancements:**  
  Improve the user interface for a more engaging chat experience, add user role-based login, and enable persistent chat history for returning users.
- **Data Pipeline:**  
  Automate periodic re-scraping and re-indexing to keep the knowledge base up to date.
- **Evaluation & Monitoring:**  
  Add analytics for user queries, retrieval accuracy, and LLM response quality.
- **Scalability:**  
  Containerize the application for easier deployment and scaling, and consider supporting additional banks or financial products.

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd BOM
```

### 2. Python Environment

- Python 3.9+ recommended.
- Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root with:

```
GOOGLE_API_KEY=your_google_gemini_api_key
PG_HOST=localhost
PG_PORT=5432
PG_DB=bom_loan_db
PG_USER=your_db_user
PG_PASSWORD=your_db_password
```

### 4. Database (PostgreSQL)

- Ensure PostgreSQL is running and accessible.
- The backend will auto-create tables on first run.

### 5. Frontend (Next.js)

```bash
cd frontend
npm install
```

---

## Usage

### 1. Web Scraping

To extract the latest loan data:

```bash
python webscrapping_scripts/script_1.py
python webscrapping_scripts/script_2.py
# ... repeat for all scripts as needed
```

Outputs are saved in `Extracteddata_scriptwise/`.

### 2. Chunking & Embedding

To process and embed the scraped data:

```bash
python rag_pipeline/chunk_and_embed.py
```

This creates/updates the FAISS index and metadata.

### 3. Start the Backend API

```bash
uvicorn app.main:app --reload
```

- API available at `http://localhost:8000`
- Test endpoint: `GET /`
- Main endpoint: `POST /ask` with JSON `{ "query": "your question" }`

### 4. Start the Frontend

```bash
cd frontend
npm run dev
```

- App available at `http://localhost:3000`
- Interacts with backend at `/ask`

---

## Commands

| Task                        | Command                                                      |
|-----------------------------|--------------------------------------------------------------|
| Install Python deps         | `pip install -r requirements.txt`                            |
| Install Node deps           | `cd frontend && npm install`                                 |
| Run web scraping            | `python webscrapping_scripts/script_X.py`                    |
| Chunk & embed data          | `python rag_pipeline/chunk_and_embed.py`                     |
| Start backend (FastAPI)     | `uvicorn app.main:app --reload`                              |
| Start frontend (Next.js)    | `cd frontend && npm run dev`                                 |
| Run RAG engine CLI          | `python rag_pipeline/rag_engine.py`                          |
| View logs                   | `tail -f logs/build.log` (or open in any text editor)        |

---

## Development & Logs

- All logs (backend, RAG, chunking) are written to `logs/build.log`.
- Database tables are auto-created if not present.
- Update `.env` for API keys and DB credentials.

---

## Contributing

1. Fork the repo and create your branch.
2. Commit your changes with clear messages.
3. Ensure all scripts and services run without errors.
4. Submit a pull request.


---

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Google Gemini](https://ai.google.dev/)
- [FAISS](https://faiss.ai/)
- [Playwright](https://playwright.dev/python/)

---

## Contact

For questions or support, open an issue or contact the maintainer.
