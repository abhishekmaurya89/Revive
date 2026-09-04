from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI


llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    temperature=0,
    google_api_key=settings.google_api_key,
)
