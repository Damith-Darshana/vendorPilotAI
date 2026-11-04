import os
from sqlalchemy import create_engine, text
from config import settings

def wake_up_db():
    print("Connecting to wake up Neon database (this may take a few seconds if it's sleeping)...")
    
    # Create engine with a longer timeout specifically for waking up
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"connect_timeout": 15}
    )
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"Database woke up successfully! Test query result: {result.scalar()}")

if __name__ == "__main__":
    wake_up_db()