from services.user_service import login

result = login(
    username="test_qr_2",
    password="6>mK_P=Yp!buR[6HC(D!Aw$j",
    totp_code="776747"
)

print(result)