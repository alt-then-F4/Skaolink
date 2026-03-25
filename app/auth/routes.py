from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, limiter
from app.models import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)


# ─── RBAC DECORATOR ─────────────────────────────────────────
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not any(r.nom in roles for r in current_user.roles):
                return 'Accès interdit', 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ─── USER LOADER ────────────────────────────────────────────
from app import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── REGISTER ───────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'etudiant')

        if not all([nom, prenom, email, password]):
            return 'Tous les champs sont requis', 400

        if role not in ['admin', 'prof', 'etudiant']:
            return 'Rôle invalide', 400

        if User.query.filter_by(email=email).first():
            return 'Email déjà utilisé', 400

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(nom=nom, prenom=prenom, email=email,
                    password_hash=password_hash, role=role)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return '''
        <form method="POST">
            <input name="nom" placeholder="Nom" required><br>
            <input name="prenom" placeholder="Prénom" required><br>
            <input name="email" type="email" placeholder="Email" required><br>
            <input name="password" type="password" placeholder="Mot de passe" required><br>
            <select name="role">
                <option value="etudiant">Étudiant</option>
                <option value="prof">Professeur</option>
                <option value="admin">Administrateur</option>
            </select><br>
            <button type="submit">S'inscrire</button>
        </form>
    '''


# ─── LOGIN ──────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return 'Email ou mot de passe incorrect', 401

        login_user(user)

        if any(r.nom == 'admin' for r in user.roles):
            return redirect(url_for('admin.index'))
        elif any(r.nom == 'prof' for r in user.roles):
            return redirect(url_for('prof.index'))
        else:
            return redirect(url_for('etudiant.index'))

    return '''
        <form method="POST">
            <input name="email" type="email" placeholder="Email" required><br>
            <input name="password" type="password" placeholder="Mot de passe" required><br>
            <button type="submit">Se connecter</button>
        </form>
    '''


# ─── LOGOUT ─────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
