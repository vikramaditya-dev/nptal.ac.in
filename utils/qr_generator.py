import qrcode
from PIL import Image

def generate_qr_image(url: str) -> Image.Image:
    """
    Generate a QR code and return it as a PIL Image object.
    Caller is responsible for saving/uploading.
    """
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img


def generate_qr(url: str, output_path: str) -> None:
    """Legacy helper — saves QR to a local path (kept for compatibility)."""
    img = generate_qr_image(url)
    img.save(output_path)
