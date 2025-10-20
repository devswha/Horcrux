#!/usr/bin/env python3
"""
Apply pgvector migration to Supabase database
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2-binary not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        print("❌ SUPABASE_URL not found in .env")
        sys.exit(1)

    print(f"🔗 Connecting to Supabase...")

    try:
        conn = psycopg2.connect(supabase_url)
        cursor = conn.cursor()

        # Read migration file
        migration_path = Path(__file__).parent.parent / "migrations" / "001_add_pgvector_support.sql"
        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        print(f"📝 Applying migration: {migration_path.name}")

        # Execute migration
        cursor.execute(migration_sql)
        conn.commit()

        print("✅ Migration applied successfully!")

        # Verify pgvector extension
        cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print(f"✅ pgvector extension enabled: version {result[1]}")
        else:
            print("⚠️  pgvector extension not found")

        # Verify embedding column
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'conversation_memory' AND column_name = 'embedding';
        """)
        result = cursor.fetchone()
        if result:
            print(f"✅ embedding column added: {result[0]} ({result[1]})")
        else:
            print("⚠️  embedding column not found")

        # Verify index
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'conversation_memory' AND indexname = 'conversation_memory_embedding_idx';
        """)
        result = cursor.fetchone()
        if result:
            print(f"✅ Vector index created: {result[0]}")
        else:
            print("⚠️  Vector index not found")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
