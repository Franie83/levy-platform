# check_qr.py
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.filter_by(role='payee').all()
    print("Payee users:")
    for user in users:
        print(f"  {user.name}: QR Code = {user.qr_code}")