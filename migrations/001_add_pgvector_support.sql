-- Migration: Add pgvector support for RAG system
-- Phase 1: Enable pgvector extension and add embedding column

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to conversation_memory table (1536 dimensions for text-embedding-3-small)
ALTER TABLE conversation_memory
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for fast similarity search using HNSW (better than IVFFlat for most cases)
CREATE INDEX IF NOT EXISTS conversation_memory_embedding_idx
ON conversation_memory
USING hnsw (embedding vector_cosine_ops);

-- Alternative: IVFFlat index (uncomment if HNSW causes issues)
-- CREATE INDEX IF NOT EXISTS conversation_memory_embedding_idx
-- ON conversation_memory
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);
