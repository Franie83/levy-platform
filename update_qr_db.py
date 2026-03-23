# update_qr_db.py
from app import create_app
from app.models import User
import os

app = create_app()
with app.app_context():
    users = User.query.filter_by(role='payee').all()
    
    for user in users:
        qr_filename = f'user_qr_{user.id}_{user.nin}.png'
        qr_path = os.path.join('app', 'static', 'uploads', 'qrcodes', 'users', qr_filename)
        
        if os.path.exists(qr_path):
            user.qr_code = qr_filename
            print(f'✅ Updated: {user.name} -> {qr_filename}')
        else:
            print(f'❌ File not found for {user.name}: {qr_path}')
    
    from app import db
    db.session.commit()
    print('\n✅ Database updated with QR code filenames!')