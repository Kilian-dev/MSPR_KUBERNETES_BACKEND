import os
import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()


def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "MSPR_2"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


@pytest.fixture(scope="session", autouse=True)
def clean_test_user():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = 'ci_test_user'")
    conn.commit()
    cur.close()
    conn.close()
    yield
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = 'ci_test_user'")
    conn.commit()
    cur.close()
    conn.close()
