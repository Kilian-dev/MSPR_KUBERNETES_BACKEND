from services.user_service import register_user
from utils.qrcode_utils import save_qr_code_png

result = register_user("test_qr_2")

password = result["password"]

save_qr_code_png(password, "password_qr.png")

print("Mot de passe :", password)
print("QR généré dans password_qr.png")