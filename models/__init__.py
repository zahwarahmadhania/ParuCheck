from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# Junction Table for Many-to-Many relationship between Rule and Symptom
rule_symptoms = db.Table('rule_symptoms',
    db.Column('rule_id', db.Integer, db.ForeignKey('rule.id', ondelete='CASCADE'), primary_key=True),
    db.Column('symptom_id', db.Integer, db.ForeignKey('symptom.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='patient')  # 'admin' or 'patient'
    status = db.Column(db.String(50), default='active')  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    diagnoses = db.relationship('DiagnosisHistory', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Symptom(db.Model):
    __tablename__ = 'symptom'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # e.g., G001
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # e.g., 'Umum', 'Pernapasan'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Symptom {self.code}: {self.name}>"

class Disease(db.Model):
    __tablename__ = 'disease'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # e.g., P001
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    causes = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    prevention = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rules = db.relationship('Rule', backref='disease', cascade='all, delete-orphan', lazy=True)
    diagnoses = db.relationship('DiagnosisHistory', backref='disease', lazy=True)
    
    def __repr__(self):
        return f"<Disease {self.code}: {self.name}>"

class Rule(db.Model):
    __tablename__ = 'rule'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # e.g., R001
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Many-to-many relationship with Symptom
    symptoms = db.relationship('Symptom', secondary=rule_symptoms, lazy='subquery',
                               backref=db.backref('rules', lazy=True))
    
    def __repr__(self):
        return f"<Rule {self.code} -> Disease ID {self.disease_id}>"

class DiagnosisHistory(db.Model):
    __tablename__ = 'diagnosis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    patient_name = db.Column(db.String(255), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_gender = db.Column(db.String(50), nullable=False)
    symptoms_json = db.Column(db.Text, nullable=False)  # JSON-encoded array of symptom names/codes
    diagnosed_disease_id = db.Column(db.Integer, db.ForeignKey('disease.id', ondelete='SET NULL'), nullable=True)
    confidence_percentage = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def symptoms_list(self):
        try:
            return json.loads(self.symptoms_json)
        except Exception:
            return []
            
    @symptoms_list.setter
    def symptoms_list(self, value):
        self.symptoms_json = json.dumps(value)
        
    def __repr__(self):
        return f"<DiagnosisHistory ID {self.id} for {self.patient_name}>"
