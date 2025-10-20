"""
Embedding service for RAG system
Uses OpenAI text-embedding-3-small model
"""
import os
from typing import List, Optional
from openai import OpenAI


class EmbeddingService:
    """임베딩 생성 서비스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding service

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536  # text-embedding-3-small default dimensions

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of 1536 float values representing the embedding vector

        Raises:
            ValueError: If text is empty
            Exception: If OpenAI API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                encoding_format="float"
            )
            return response.data[0].embedding

        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch (more efficient)

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors, one per input text

        Raises:
            ValueError: If texts list is empty
            Exception: If OpenAI API call fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        # Filter out empty strings
        filtered_texts = [t.strip() for t in texts if t and t.strip()]
        if not filtered_texts:
            raise ValueError("All texts are empty after filtering")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=filtered_texts,
                encoding_format="float"
            )

            # Sort by index to maintain order
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [emb.embedding for emb in embeddings]

        except Exception as e:
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")

    def calculate_cost(self, text_count: int, avg_tokens_per_text: int = 50) -> float:
        """
        Estimate embedding cost

        Args:
            text_count: Number of texts to embed
            avg_tokens_per_text: Average tokens per text (default: 50)

        Returns:
            Estimated cost in USD

        Note:
            text-embedding-3-small pricing: $0.02 per 1M tokens
        """
        total_tokens = text_count * avg_tokens_per_text
        cost_per_million = 0.02
        return (total_tokens / 1_000_000) * cost_per_million


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from dotenv import load_dotenv
    load_dotenv()

    # Test embedding service
    service = EmbeddingService()

    # Single text
    print("Testing single embedding...")
    text = "어제 7시간 잤고 30분 운동했어"
    embedding = service.generate_embedding(text)
    print(f"✓ Generated embedding: {len(embedding)} dimensions")
    print(f"  First 5 values: {embedding[:5]}")

    # Batch
    print("\nTesting batch embeddings...")
    texts = [
        "이창하는 대학교 때 친해진 형이야",
        "오늘 프로그래밍 공부했어",
        "내일 회의가 있어"
    ]
    embeddings = service.generate_embeddings_batch(texts)
    print(f"✓ Generated {len(embeddings)} embeddings")
    for i, emb in enumerate(embeddings):
        print(f"  Text {i+1}: {len(emb)} dimensions")

    # Cost estimation
    print("\nCost estimation:")
    cost = service.calculate_cost(text_count=1000)
    print(f"  1,000 texts: ${cost:.4f}")
    cost = service.calculate_cost(text_count=10000)
    print(f"  10,000 texts: ${cost:.4f}")
