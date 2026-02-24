from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    env: str = "dev"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    groq_api_key: str
    
    database_url: str = "sqlite:///./askbase.db"
    
    cors_origins: str = "http://localhost:5173"
    
    # Cohere API for embeddings (free tier: 100 calls/min)
    cohere_api_key: str = ""
    
    default_page_size: int = 20
    max_page_size: int = 100
    
    max_file_size_mb: int = 10
    
    # Optimized for free tier deployment
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    use_mmr: bool = True
    mmr_diversity: float = 0.3
    mmr_fetch_k: int = 20
    retrieval_k: int = 6
    
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1500

    class Config:
        env_file = ".env"

settings = Settings()