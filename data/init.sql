-- Smart Bookmark Manager Database Initialization
-- This script runs automatically on first database startup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create bookmarks table
CREATE TABLE IF NOT EXISTS bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    categories JSONB NOT NULL DEFAULT '[]',
    image_url TEXT,
    embedding vector(1536),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at DESC);

-- Create index on URL for duplicate detection
CREATE INDEX IF NOT EXISTS idx_bookmarks_url ON bookmarks(url);

-- Create HNSW index on embeddings for fast similarity search
CREATE INDEX IF NOT EXISTS idx_bookmarks_embedding ON bookmarks USING hnsw (embedding vector_cosine_ops);

-- Create collections table
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#007bff',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_user_id ON collections(user_id);

-- Create bookmark_collections many-to-many relationship table
CREATE TABLE IF NOT EXISTS bookmark_collections (
    bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY (bookmark_id, collection_id)
);

CREATE INDEX IF NOT EXISTS idx_bookmark_collections_bookmark ON bookmark_collections(bookmark_id);
CREATE INDEX IF NOT EXISTS idx_bookmark_collections_collection ON bookmark_collections(collection_id);
