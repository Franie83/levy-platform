from flask import Blueprint 
 
bp = Blueprint('admin_param', __name__, url_prefix='/admin-param') 
 
@bp.route('/') 
def index(): 
    return "Parameter Test Blueprint is working!" 
 
def test_param(test_id): 
    return f"Test parameter received: {test_id}" 
