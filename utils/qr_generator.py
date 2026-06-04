import qrcode

def generate_qr(url: str, output_path: str) -> None:
    """Generate a standard black-and-white certificate QR code."""

    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("RGB")

    img.save(output_path)