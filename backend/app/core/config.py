from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    env: str = "dev"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    hf_api_key: str = ""
    hf_model: str = ""
    groq_api_key: str
    
    database_url: str = "sqlite:///./askbase.db"
    
    cors_origins: str = "http://localhost:5173"
    
    default_page_size: int = 20
    max_page_size: int = 100
    
    max_file_size_mb: int = 10
    
    # Optimized for free tier deployment
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Lightweight model optimized for free tier (80MB)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    use_mmr: bool = True
    mmr_diversity: float = 0.3
    mmr_fetch_k: int = 20
    retrieval_k: int = 6
    
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1500

    class Config:
        env_file = ".env"

settings = Settings()