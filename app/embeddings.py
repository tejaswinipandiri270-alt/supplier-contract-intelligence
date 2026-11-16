from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import get_settings

@lru_cache
def get_model():
    return SentenceTransformer(get_settings().embedding_model)

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()

def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
