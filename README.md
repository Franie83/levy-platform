# Levy Management Platform 
 
A comprehensive platform for managing daily levies, business registration, vehicle registration, and payment processing. 
 
## Features 
 
- ? **User Authentication** with roles (MSME, Transporter, Enforcer, Super Admin) 
- ? **Business Registration** for MSME users 
- ? **Vehicle Registration** for Transporter users 
- ? **Payment Processing** with Paystack integration (simulation mode) 
- ? **QR Code Receipts** for payment verification 
- ? **Admin Dashboard** with full CRUD operations 
- ? **Search and Filter** for all entities 
- ? **Role-based Access Control** 
 
## Technology Stack 
 
- **Backend**: Python Flask 
- **Database**: SQLite (development) 
- **Frontend**: HTML, Bootstrap 5, JavaScript 
- **Authentication**: Flask-Login 
- **Payment**: Paystack (simulated) 
 
## Installation 
 
1. Clone the repository: 
\`\`\`bash 
git clone https://github.com/Franie83/levy-platform.git 
cd levy-platform 
\`\`\` 
 
2. Create and activate virtual environment: 
\`\`\`bash 
python -m venv venv 
venv\Scripts\activate  # On Windows 
\`\`\` 
 
3. Install dependencies: 
\`\`\`bash 
pip install -r requirements.txt 
\`\`\` 
 
4. Set up environment variables: 
\`\`\`bash 
cp .env.example .env 
# Edit .env with your configuration 
\`\`\` 
 
5. Initialize the database: 
\`\`\`bash 
python 
from app import create_app, db 
app = create_app() 
with app.app_context(): 
    db.create_all() 
exit() 
\`\`\` 
 
6. Create default users: 
\`\`\`bash 
python create_default_users.py 
\`\`\` 
 
7. Run the application: 
\`\`\`bash 
python app.py 
\`\`\` 
 
## Default Users 
 
 
## License 
MIT 
"# Digital-Payment-Platform" 
"# Digital-Payment-Platform" 
