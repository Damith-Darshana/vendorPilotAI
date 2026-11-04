import os 
from dotenv import load_dotenv

load_dotenv()

# Fail fast if the key is missing
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is not set in .env file")

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is not set in .env file")

if not os.getenv("DATABASE_URL"):
    raise ValueError("DATABASE_URL is not set in .env file")

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL =  os.getenv("DATABASE_URL")

settings = Settings()