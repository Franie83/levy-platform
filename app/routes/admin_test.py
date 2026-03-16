from flask import Blueprint 
 
bp = Blueprint('admin_test', __name__, url_prefix='/admin-test') 
 
@bp.route('/') 
def index(): 
    return "Admin test blueprint is working!" 
 
@bp.route('/test') 
def test(): 
    return "Test route is working!" 
