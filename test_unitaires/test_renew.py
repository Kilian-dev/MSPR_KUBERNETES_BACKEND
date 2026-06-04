from services.user_service import renew_credentials
from utils.qrcode_utils import save_qr_code_png

result = renew_credentials("test_qr_2")

print(result["success"])
print("Nouveau password :", result["password"])

save_qr_code_png(result["password"], "renew_password_qr.png")
save_qr_code_png(result["totp_uri"], "renew_mfa_qr.png")

print("QR générés")