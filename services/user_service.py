from database.connection import get_connection
from utils.qrcode_utils import generate_qr_code_base64
from utils.security import (
    generate_password,
    hash_password
)
from utils.security import generate_mfa_secret, generate_totp_uri
from utils.qrcode_utils import generate_qr_code_base64
from utils.security import (
    verify_password,
    verify_totp
)

from datetime import datetime, timedelta

from utils.security import (
    generate_password,
    hash_password,
    verify_password,
    generate_mfa_secret,
    generate_totp_uri,
    verify_totp
)




def renew_credentials(username: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username = %s",
        (username,)
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Utilisateur introuvable"
        }

    password = generate_password()
    hashed_password = hash_password(password)

    mfa_secret = generate_mfa_secret()
    totp_uri = generate_totp_uri(username, mfa_secret)

    password_qr_code = generate_qr_code_base64(password)
    mfa_qr_code = generate_qr_code_base64(totp_uri)

    cur.execute(
        """
        UPDATE users
        SET password = %s,
            mfa = %s,
            gen_date = CURRENT_TIMESTAMP,
            expired = FALSE
        WHERE username = %s
        """,
        (hashed_password, mfa_secret, username)
    )

    conn.commit()

    cur.close()
    conn.close()

    return {
        "success": True,
        "username": username,
        "password": password,
        "password_qr_code": password_qr_code,
        "mfa_secret": mfa_secret,
        "mfa_qr_code": mfa_qr_code,
        "totp_uri": totp_uri
    }


def login(username: str, password: str, totp_code: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT password, mfa, gen_date, expired
        FROM users
        WHERE username = %s
        """,
        (username,)
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Utilisateur introuvable"
        }

    hashed_password, mfa_secret, gen_date, expired = user

    # Vérifie si déjà expiré
    if expired:
        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Compte expiré"
        }

    # Vérifie expiration 6 mois
    six_months = timedelta(days=180)

    if datetime.now() - gen_date > six_months:

        cur.execute(
            """
            UPDATE users
            SET expired = TRUE
            WHERE username = %s
            """,
            (username,)
        )

        conn.commit()

        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Credentials expirés"
        }

    # Vérifie password
    if not verify_password(password, hashed_password):

        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Mot de passe invalide"
        }

    # Vérifie TOTP
    if not verify_totp(mfa_secret, totp_code):

        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Code MFA invalide"
        }

    cur.close()
    conn.close()

    return {
        "success": True,
        "message": "Connexion réussie"
    }

def generate_mfa(username: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username = %s",
        (username,)
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return {
            "success": False,
            "message": "Utilisateur introuvable"
        }

    secret = generate_mfa_secret()
    totp_uri = generate_totp_uri(username, secret)
    qr_code = generate_qr_code_base64(totp_uri)

    cur.execute(
        "UPDATE users SET mfa = %s WHERE username = %s",
        (secret, username)
    )

    conn.commit()

    cur.close()
    conn.close()

    return {
        "success": True,
        "username": username,
        "mfa_secret": secret,
        "mfa_qr_code": qr_code,
        "totp_uri": totp_uri
    }

def register_user(username: str):

    conn = get_connection()
    cur = conn.cursor()

    # Vérifie si le user existe déjà
    cur.execute(
        "SELECT id FROM users WHERE username = %s",
        (username,)
    )

    existing_user = cur.fetchone()

    if existing_user:
        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Utilisateur déjà existant"
        }

    # Génération password
    password = generate_password()

    # Hash password
    hashed_password = hash_password(password)

    # Insert DB
    cur.execute(
        """
        INSERT INTO users (
            username,
            password
        )
        VALUES (%s, %s)
        RETURNING id
        """,
        (username, hashed_password)
    )

    user_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "success": True,
        "user_id": user_id,
        "username": username,
        "password": password,
        "password_qr_code": generate_qr_code_base64(password)
    }