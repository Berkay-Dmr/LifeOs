from app.config.settings import get_settings
from app.database.sqlite import init_db, get_connection

settings = get_settings()
init_db(settings.db_path)

with get_connection() as conn:
    # Check schema
    schema = conn.execute("PRAGMA table_info(chunks)").fetchall()
    print("Chunks schema:", [s[1] for s in schema])

    # Check transkript chunks
    rows = conn.execute("""
        SELECT d.path, c.text
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.path LIKE '%transkript%'
    """).fetchall()
    print(f"\nTranskript chunks: {len(rows)}")
    for path, content in rows:
        print(f"\n--- {path} ---")
        print(content[:500] if content else "NO TEXT")
