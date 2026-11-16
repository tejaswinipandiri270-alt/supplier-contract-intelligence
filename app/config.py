from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    top_k: int = 8
    min_retrieval_score: float = 0.15
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_index: str = "supplier-contract-chunks"
    opensearch_username: str = ""
    opensearch_password: str = ""
    opensearch_use_ssl: bool = False
    opensearch_verify_certs: bool = False

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = ""

    aws_region: str = "eu-west-2"
    s3_bucket: str = ""
    s3_prefix: str = "supplier-contracts/"
    use_s3: bool = False
    aws_opensearch_host: str = ""
    aws_opensearch_username: str = ""
    aws_opensearch_password: str = ""
    aws_opensearch_use_aws_auth: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def search_host(self):
        return self.aws_opensearch_host or self.opensearch_host

    @property
    def search_username(self):
        return self.aws_opensearch_username or self.opensearch_username

    @property
    def search_password(self):
        return self.aws_opensearch_password or self.opensearch_password

    @property
    def use_ssl(self):
        return bool(self.aws_opensearch_host) or self.opensearch_use_ssl

@lru_cache
def get_settings():
    return Settings()
