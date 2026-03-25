from app import db
from flask_login import UserMixin
from datetime import datetime

# ─── TABLE ASSOCIATION USER <-> ROLES ────────────────────────
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# ─── ROLES ──────────────────────────────────────────────────
class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Enum('admin', 'prof', 'etudiant'), unique=True, nullable=False)

# ─── UTILISATEURS ───────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship('Role', secondary=user_roles, backref='users', lazy=True)
    notes = db.relationship('Note', backref='etudiant', lazy=True,
                            foreign_keys='Note.etudiant_id')
    absences = db.relationship('Absence', backref='etudiant', lazy=True,
                               foreign_keys='Absence.etudiant_id')

    def has_role(self, role_nom):
        return any(r.nom == role_nom for r in self.roles)

    def get_roles(self):
        return [r.nom for r in self.roles]

# ─── CLASSES ────────────────────────────────────────────────
class Classe(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)

    etudiants = db.relationship('Inscription', backref='classe', lazy=True)
    cours = db.relationship('Cours', backref='classe', lazy=True)

# ─── INSCRIPTIONS ───────────────────────────────────────────
class Inscription(db.Model):
    __tablename__ = 'inscriptions'

    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    classe_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

# ─── COURS ──────────────────────────────────────────────────
class Cours(db.Model):
    __tablename__ = 'cours'

    id = db.Column(db.Integer, primary_key=True)
    matiere = db.Column(db.String(100), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    classe_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    jour = db.Column(db.Enum('lundi','mardi','mercredi','jeudi','vendredi'), nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)

    evaluations = db.relationship('Evaluation', backref='cours', lazy=True)
    absences = db.relationship('Absence', backref='cours', lazy=True)

# ─── EVALUATIONS ────────────────────────────────────────────
class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)
    cours_id = db.Column(db.Integer, db.ForeignKey('cours.id'), nullable=False)
    coefficient = db.Column(db.Float, default=1.0)

    notes = db.relationship('Note', backref='evaluation', lazy=True)

# ─── NOTES ──────────────────────────────────────────────────
class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=False)
    valeur = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('etudiant_id', 'evaluation_id', name='unique_note'),
    )

# ─── ABSENCES ───────────────────────────────────────────────
class Absence(db.Model):
    __tablename__ = 'absences'

    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cours_id = db.Column(db.Integer, db.ForeignKey('cours.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    justifiee = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─── DEVOIRS ────────────────────────────────────────────────
class Devoir(db.Model):
    __tablename__ = 'devoirs'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_rendu = db.Column(db.Date, nullable=False)
    cours_id = db.Column(db.Integer, db.ForeignKey('cours.id'), nullable=False)
