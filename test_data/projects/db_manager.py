import os

def connect_to_db():
    """Connect to PostgreSQL database."""
    url = os.environ.get("DATABASE_URL", "localhost:5432")
    return url

class DatabaseManager:
    def __init__(self):
        self.connection = None

    def connect(self):
        self.connection = connect_to_db()
        return self.connection

    def disconnect(self):
        self.connection = None
