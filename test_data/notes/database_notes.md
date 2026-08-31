# Database Notes

## PostgreSQL

PostgreSQL is a powerful open source relational database.

### Connection

To connect to PostgreSQL:
```python
import psycopg2
conn = psycopg2.connect("dbname=mydb user=postgres")
```

### Docker

Run PostgreSQL in Docker:
```yaml
services:
  db:
    image: postgres
```

## Redis

Redis is an in-memory data store used for caching.
