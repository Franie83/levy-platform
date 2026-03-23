# create_test_qr.py
import qrcode
import os

# Create a test QR code with a receipt number
receipt_number = "RCP0DD56BE604C6"
qr = qrcode.make(receipt_number)
qr.save("test_qr.png")
print(f"✅ Test QR code created: test_qr.png with receipt: {receipt_number}")