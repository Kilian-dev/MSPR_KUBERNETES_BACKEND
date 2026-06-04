import json, psycopg2, pyotp, qrcode, io, base64

def read_secret(name):
    with open(f'/var/openfaas/secrets/{name}', 'r') as f:
        return f.read().strip()

def get_connection():
    return psycopg2.connect(
        host=read_secret('host'), port=read_secret('port'),
        dbname=read_secret('dbname'), user=read_secret('user'),
        password=read_secret('password')
    )

def generate_qr_base64(data):
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def handle(event, context):
    try:
        body = json.loads(event.body)
        username = body.get('username')
        if not username:
            return {"statusCode": 400, "body": json.dumps({"success": False, "message": "username requis"})}
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if not cur.fetchone():
            cur.close(); conn.close()
            return {"statusCode": 404, "body": json.dumps({"success": False, "message": "Utilisateur introuvable"})}
        secret = pyotp.random_base32()
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="COFRAP")
        cur.execute("UPDATE users SET mfa = %s WHERE username = %s", (secret, username))
        conn.commit(); cur.close(); conn.close()
        return {"statusCode": 200, "body": json.dumps({
            "success": True, "username": username, "mfa_secret": secret,
            "mfa_qr_code": generate_qr_base64(totp_uri), "totp_uri": totp_uri
        })}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"success": False, "message": str(e)})}
