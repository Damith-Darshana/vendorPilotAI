import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.database import Base, engine
from src.db.models import Case,Document,Finding,AuditLog
from langgraph.checkpoint.postgres import PostgresSaver
from src.config import settings
from sqlalchemy import text

def init():
  with engine.connect() as conn:
    conn.execute(text(
        "ALTER TABLE findings ADD COLUMN IF NOT EXISTS page_number INTEGER"
    ))
    conn.commit()

  print("creating application tables...")
  Base.metadata.create_all(bind=engine)
  print("  Cases, Documents, Findings, AuditLogs created.")

  print("Setting up LangGraph checkpoint tables...")
  with PostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
       checkpointer.setup()
  print("  Checkpoint tables ready.")

  print("\nDatabase initialized successfully.")

if __name__ == "__main__":
    init()
       