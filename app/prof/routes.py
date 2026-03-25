from flask import Blueprint

prof_bp = Blueprint('prof', __name__)

@prof_bp.route('/')
def index():
    return 'Prof dashboard - coming soon'
