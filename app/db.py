# app/db.py

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, TIMESTAMP, func
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "bom_loan_db")
PG_USER = os.getenv("PG_USER", "saurabh")
PG_PASSWORD = os.getenv("PG_PASSWORD", "saurabh")

DATABASE_URL = (
    f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

# Create the table if it doesn't exist
try:
    Base.metadata.create_all(engine)
except SQLAlchemyError as e:
    print(f"Error creating tables: {e}")

def log_query(question: str, response: str):
    """Insert a new query log into the database."""
    session = SessionLocal()
    try:
        log = QueryLog(question=question, response=response)
        session.add(log)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error logging query: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Table created!")
