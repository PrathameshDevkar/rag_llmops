from langgraph.checkpoint.postgres import PostgresSaver
from backend.app.core.config import settings
from backend.app.core.database import engine
from contextlib import contextmanager

@contextmanager
def get_checkpointer():
    with PostgresSaver.from_conn_string(settings.psycopg_URL) as saver:
        yield saver
