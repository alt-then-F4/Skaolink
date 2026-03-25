from flask import Blueprint

etudiant_bp = Blueprint('etudiant', __name__)

@etudiant_bp.route('/')
def index():
    return 'Etudiant dashboard - coming soon'
