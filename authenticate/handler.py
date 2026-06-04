import json, psycopg2, hashlib, pyotp
from datetime import datetime, timedelta

def read_secret(name):
    with open(f'/var/openfaas/secrets/{name}', 'r') as f:
        return f.read().strip()

def get_connection():
    return psycopg2.connect(
        host=read_secret('host'), port=read_secret('port'),
        dbname=read_secret('dbname'), user=read_secret('user'),
        password=read_secret('password')
    )

def handle(event, context):
    try:
        body = json.loads(event.body)
        username = body.get('username')
        password = body.get('password')
        totp_code = body.get('totp_code')
        if not all([username, password, totp_code]):
            return {"statusCode": 400, "body": json.dumps({"success": False, "message": "username, password et totp_code requis"})}
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password, mfa, gen_date, expired FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user:
            cur.close(); conn.close()
            return {"statusCode": 404, "body": json.dumps({"success": False, "message": "Utilisateur introuvable"})}
        hashed_password, mfa_secret, gen_date, expired = user
        if expired:
            cur.close(); conn.close()
            return {"statusCode": 403, "body": json.dumps({"success": False, "message": "Compte expiré", "action": "renew"})}
        if datetime.now() - gen_date > timedelta(days=180):
            cur.execute("UPDATE users SET expired = TRUE WHERE username = %s", (username,))
            conn.commit(); cur.close(); conn.close()
            return {"statusCode": 403, "body": json.dumps({"success": False, "message": "Credentials expirés", "action": "renew"})}
        if hashlib.sha256(password.encode()).hexdigest() != hashed_password:
            cur.close(); conn.close()
            return {"statusCode": 401, "body": json.dumps({"success": False, "message": "Mot de passe invalide"})}
        if not pyotp.TOTP(mfa_secret).verify(totp_code):
            cur.close(); conn.close()
            return {"statusCode": 401, "body": json.dumps({"success": False, "message": "Code MFA invalide"})}
        cur.close(); conn.close()
        return {"statusCode": 200, "body": json.dumps({"success": True, "message": "Connexion réussie"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"success": False, "message": str(e)})}
