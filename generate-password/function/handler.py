import json, psycopg2, secrets, string, hashlib, qrcode, io, base64

def read_secret(name):
    with open(f'/var/openfaas/secrets/{name}', 'r') as f:
        return f.read().strip()

def get_connection():
    return psycopg2.connect(
        host=read_secret('host'), port=read_secret('port'),
        dbname=read_secret('dbname'), user=read_secret('user'),
        password=read_secret('password')
    )

def generate_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(24))
        if (any(c.isupper() for c in pwd) and any(c.islower() for c in pwd)
                and any(c.isdigit() for c in pwd) and any(c in string.punctuation for c in pwd)):
            return pwd

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        if cur.fetchone():
            cur.close(); conn.close()
            return {"statusCode": 409, "body": json.dumps({"success": False, "message": "Utilisateur déjà existant"})}
        password = generate_password()
        hashed = hash_password(password)
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", (username, hashed))
        user_id = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()
        return {"statusCode": 200, "body": json.dumps({
            "success": True, "user_id": user_id, "username": username,
            "password": password, "password_qr_code": generate_qr_base64(password)
        })}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"success": False, "message": str(e)})}
