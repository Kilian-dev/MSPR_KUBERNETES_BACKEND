from services.user_service import generate_mfa
from utils.qrcode_utils import save_qr_code_png

result = generate_mfa("test_qr_2")

save_qr_code_png(result["totp_uri"], "mfa_qr.png")

print("QR MFA généré : mfa_qr.png")
print("Secret :", result["mfa_secret"])