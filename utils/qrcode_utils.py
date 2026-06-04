import qrcode
import base64
from io import BytesIO

def save_qr_code_png(data: str, filename: str):
    image = qrcode.make(data)
    image.save(filename)


def generate_qr_code_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    

    return qr_base64