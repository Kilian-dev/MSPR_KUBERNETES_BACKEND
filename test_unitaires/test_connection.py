from database.connection import get_connection


def test_connection():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT NOW();")

    result = cur.fetchone()

    print("Connexion OK :", result[0])

    cur.close()
    conn.close()


if __name__ == "__main__":
    test_connection()