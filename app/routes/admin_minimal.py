from flask import Blueprint 
from app.models import Business 
 
bp = Blueprint('admin_minimal', __name__, url_prefix='/admin-minimal') 
 
@bp.route('/') 
def index(): 
    return "Admin Minimal is working!" 
 
@bp.route('/businesses') 
def businesses(): 
    businesses = Business.query.all() 
    html = "<h2>Businesses</h2><ul>" 
    for b in businesses: 
        html = html + "<li><a href='/admin-minimal/business/" + str(b.id) + "'>" + b.business_name + "</a></li>" 
    html = html + "</ul>" 
    return html 
 
def view_business(business_id): 
    business = Business.query.get_or_404(business_id) 
    return "<h2>" + business.business_name + "</h2><p>ID: " + str(business.id) + "</p>" 
