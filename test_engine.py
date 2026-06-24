import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from models import db, Symptom, Disease, Rule
from utils.engine import run_forward_chaining

class TestInferenceEngine(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup test flask app with in-memory SQLite
        cls.app = Flask(__name__)
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(cls.app)
        
        with cls.app.app_context():
            db.create_all()
            cls.seed_test_data()
            
    @classmethod
    def seed_test_data(cls):
        # 1. Symptoms
        cls.s_cough = Symptom(code='G001', name='Batuk Berdahak', category='Umum')
        cls.s_blood = Symptom(code='G002', name='Batuk Berdarah', category='Umum')
        cls.s_dyspnea = Symptom(code='G003', name='Sesak Napas', category='Pernapasan')
        cls.s_fever = Symptom(code='G004', name='Demam', category='Umum')
        
        db.session.add_all([cls.s_cough, cls.s_blood, cls.s_dyspnea, cls.s_fever])
        db.session.flush()
        
        # Save IDs as raw integers to avoid detached instance errors after commit
        cls.cough_id = cls.s_cough.id
        cls.blood_id = cls.s_blood.id
        cls.dyspnea_id = cls.s_dyspnea.id
        cls.fever_id = cls.s_fever.id
        
        # 2. Diseases
        cls.d_tb = Disease(code='P001', name='TBC', description='Tuberculosis profile', causes='Bacterial', treatment='Antibiotics', prevention='BCG')
        cls.d_pn = Disease(code='P002', name='Pneumonia', description='Pneumonia profile', causes='Bacterial/Viral', treatment='Rest', prevention='Vaksin')
        
        db.session.add_all([cls.d_tb, cls.d_pn])
        db.session.flush()
        
        # 3. Rules
        # Rule 1 (TBC): Cough, Blood, Fever (3 symptoms)
        cls.r1 = Rule(code='R001', disease_id=cls.d_tb.id)
        cls.r1.symptoms.extend([cls.s_cough, cls.s_blood, cls.s_fever])
        
        # Rule 2 (Pneumonia): Cough, Dyspnea, Fever (3 symptoms)
        cls.r2 = Rule(code='R002', disease_id=cls.d_pn.id)
        cls.r2.symptoms.extend([cls.s_cough, cls.s_dyspnea, cls.s_fever])
        
        db.session.add_all([cls.r1, cls.r2])
        db.session.commit()
        
    def test_empty_symptoms(self):
        with self.app.app_context():
            result = run_forward_chaining([])
            self.assertFalse(result['success'])
            self.assertIsNone(result['primary_diagnosis'])
            self.assertEqual(result['confidence'], 0.0)
            
    def test_exact_rule_matching(self):
        with self.app.app_context():
            # Select: Cough, Blood, Fever (TBC Rule antecedents)
            selected_ids = [self.cough_id, self.blood_id, self.fever_id]
            result = run_forward_chaining(selected_ids)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['primary_diagnosis'].name, 'TBC')
            self.assertEqual(result['confidence'], 100.0)
            
    def test_partial_matching_fallback(self):
        with self.app.app_context():
            # Select: Cough, Blood (Matches 2 out of 3 symptoms for TBC)
            # Match ratio: 2/3 = 66.7%
            selected_ids = [self.cough_id, self.blood_id]
            result = run_forward_chaining(selected_ids)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['primary_diagnosis'].name, 'TBC')
            self.assertEqual(result['confidence'], 66.7)
            
            # Select: Cough, Fever
            # Cough and Fever are shared by both TBC and Pneumonia (matches 2/3 for both)
            # This triggers a tie, but both will have 66.7% confidence
            selected_ids2 = [self.cough_id, self.fever_id]
            result2 = run_forward_chaining(selected_ids2)
            
            self.assertTrue(result2['success'])
            self.assertEqual(result2['confidence'], 66.7)
            self.assertIn(result2['primary_diagnosis'].name, ['TBC', 'Pneumonia'])
            
if __name__ == '__main__':
    unittest.main()
