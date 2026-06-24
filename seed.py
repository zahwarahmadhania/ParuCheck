import sys
import os

# Add the project directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from config import Config
from models import db, User, Symptom, Disease, Rule

def seed_database():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")
        
        # Check if admin already exists
        if User.query.filter_by(role='admin').first():
            print("Database already seeded.")
            return
            
        print("Seeding database...")
        
        # 1. Seed Admin User
        admin = User(
            username='admin',
            email='admin@parucheck.com',
            role='admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Seed a Patient User for testing
        patient = User(
            username='pasien',
            email='pasien@parucheck.com',
            role='patient',
            status='active'
        )
        patient.set_password('pasien123')
        db.session.add(patient)
        
        # 2. Seed Symptoms
        symptoms_data = [
            # Code, Name, Category
            ('G001', 'Batuk Berdahak', 'Umum'),
            ('G002', 'Batuk Berdarah', 'Umum'),
            ('G003', 'Sesak Napas', 'Pernapasan'),
            ('G004', 'Demam', 'Umum'),
            ('G005', 'Berat Badan Turun', 'Umum'),
            ('G006', 'Keringat Malam', 'Umum'),
            ('G007', 'Nyeri Dada', 'Pernapasan'),
            ('G008', 'Menggigil', 'Umum'),
            ('G009', 'Mengi (Napas Berbunyi "ngik")', 'Pernapasan'),
            ('G010', 'Batuk Kering (Malam Hari)', 'Umum'),
            ('G011', 'Dada Terasa Berat / Sesak', 'Pernapasan'),
            ('G012', 'Sakit Tenggorokan', 'Umum'),
            ('G013', 'Cepat Lelah / Lemas', 'Umum'),
            ('G014', 'Batuk Kronis Berdahak', 'Umum'),
            ('G015', 'Pilek / Hidung Tersumbat', 'Umum'),
            ('G016', 'Sakit Kepala', 'Umum'),
            ('G017', 'Nyeri Otot', 'Umum')
        ]
        
        symptoms = {}
        for code, name, cat in symptoms_data:
            s = Symptom(code=code, name=name, category=cat)
            db.session.add(s)
            symptoms[code] = s
            
        db.session.flush() # Populate IDs
        
        # 3. Seed Diseases
        diseases_data = [
            {
                'code': 'P001',
                'name': 'Tuberkulosis (TBC)',
                'description': 'Tuberkulosis (TBC) adalah penyakit menular paru-paru yang disebabkan oleh infeksi bakteri Mycobacterium tuberculosis.',
                'causes': 'Bakteri Mycobacterium tuberculosis yang menyebar di udara melalui percikan dahak atau bersin penderita TBC aktif.',
                'treatment': 'Konsumsi obat anti-tuberkulosis (OAT) secara rutin dan tanpa putus selama minimal 6 bulan, di bawah pengawasan langsung dokter.',
                'prevention': 'Pemberian vaksin BCG untuk bayi, menggunakan masker di tempat umum, menjaga sirkulasi udara (ventilasi) rumah tetap baik, dan menutup mulut/hidung saat batuk.'
            },
            {
                'code': 'P002',
                'name': 'Pneumonia (Radang Paru)',
                'description': 'Pneumonia adalah infeksi yang memicu peradangan pada kantong udara (alveoli) di salah satu atau kedua paru-paru, yang dapat terisi dengan cairan atau nanah.',
                'causes': 'Infeksi bakteri (seperti Streptococcus pneumoniae), virus (seperti virus influenza), atau jamur.',
                'treatment': 'Pemberian antibiotik (untuk bakteri) atau antivirus (untuk virus), obat pereda demam dan batuk, istirahat total, serta hidrasi yang cukup.',
                'prevention': 'Vaksinasi pneumonia (PCV) dan influenza, rajin mencuci tangan, tidak merokok, dan menjaga kekebalan tubuh tetap prima.'
            },
            {
                'code': 'P003',
                'name': 'Asma',
                'description': 'Asma adalah kondisi kronis pada saluran pernapasan yang ditandai dengan peradangan, pembengkakan, dan penyempitan saluran napas, yang menyebabkan kesulitan bernapas.',
                'causes': 'Sensitivitas saluran pernapasan terhadap pemicu lingkungan seperti debu, bulu hewan, polutan udara, asap rokok, udara dingin, atau stres.',
                'treatment': 'Penggunaan inhaler pereda (pelega instan) saat serangan terjadi dan inhaler pengontrol harian untuk meredakan inflamasi jangka panjang.',
                'prevention': 'Mengidentifikasi dan menghindari pemicu alergi (alergen), menjaga kebersihan lingkungan rumah dari debu, serta tidak merokok.'
            },
            {
                'code': 'P004',
                'name': 'Bronkitis',
                'description': 'Bronkitis adalah peradangan pada mukosa atau lapisan dalam bronkus (saluran udara utama yang mengarah ke paru-paru).',
                'causes': 'Infeksi virus yang serupa dengan penyebab flu/pilek, serta paparan asap rokok atau polusi udara berkepanjangan.',
                'treatment': 'Istirahat yang cukup, perbanyak minum air hangat, obat pengencer dahak (mukolitik) atau pereda batuk, dan inhalasi uap hangat.',
                'prevention': 'Hindari asap rokok dan polusi, rutin mencuci tangan, memakai masker di lingkungan berdebu, dan dapatkan vaksin flu.'
            },
            {
                'code': 'P005',
                'name': 'PPOK (Penyakit Paru Obstruktif Kronis)',
                'description': 'PPOK adalah penyakit paru obstruktif menahun yang menghalangi aliran udara di paru-paru secara progresif, menyebabkan sesak napas yang menetap.',
                'causes': 'Paparan jangka panjang terhadap zat iritan paru, terutama asap rokok (perokok aktif maupun pasif), debu industri, atau asap pembakaran bahan bakar.',
                'treatment': 'Terapi bronkodilator untuk melegakan napas, terapi oksigen jika diperlukan, rehabilitasi paru, serta penghentian kebiasaan merokok secara total.',
                'prevention': 'Langkah pencegahan utama adalah tidak merokok, menghindari paparan polusi udara/zat kimia berbahaya di tempat kerja dengan alat pelindung diri.'
            },
            {
                'code': 'P006',
                'name': 'Influenza (Flu)',
                'description': 'Influenza adalah infeksi virus akut yang menyerang sistem pernapasan (hidung, tenggorokan, dan paru-paru).',
                'causes': 'Infeksi virus influenza tipe A, B, atau C.',
                'treatment': 'Istirahat yang cukup, konsumsi air putih melimpah, obat penurun demam dan pereda nyeri (seperti parasetamol), serta obat pereda hidung tersumbat.',
                'prevention': 'Mendapatkan vaksin flu tahunan, rajin mencuci tangan dengan sabun, menghindari kontak dekat dengan orang sakit, dan menerapkan etika batuk.'
            }
        ]
        
        diseases = {}
        for d_info in diseases_data:
            d = Disease(
                code=d_info['code'],
                name=d_info['name'],
                description=d_info['description'],
                causes=d_info['causes'],
                treatment=d_info['treatment'],
                prevention=d_info['prevention']
            )
            db.session.add(d)
            diseases[d_info['code']] = d
            
        db.session.flush() # Populate IDs
        
        # 4. Seed Rules
        # Mapping Rules (Antecedents -> Consequent)
        rules_data = [
            {
                'code': 'R001',
                'disease_code': 'P001', # TBC
                'symptom_codes': ['G001', 'G002', 'G004', 'G005', 'G006', 'G007']
            },
            {
                'code': 'R002',
                'disease_code': 'P002', # Pneumonia
                'symptom_codes': ['G001', 'G003', 'G004', 'G007', 'G008', 'G013']
            },
            {
                'code': 'R003',
                'disease_code': 'P003', # Asma
                'symptom_codes': ['G003', 'G009', 'G010', 'G011']
            },
            {
                'code': 'R004',
                'disease_code': 'P004', # Bronkitis
                'symptom_codes': ['G001', 'G003', 'G004', 'G012', 'G013']
            },
            {
                'code': 'R005',
                'disease_code': 'P005', # PPOK
                'symptom_codes': ['G003', 'G009', 'G011', 'G014']
            },
            {
                'code': 'R006',
                'disease_code': 'P006', # Influenza
                'symptom_codes': ['G004', 'G010', 'G012', 'G015', 'G016', 'G017']
            }
        ]
        
        for r_info in rules_data:
            r = Rule(
                code=r_info['code'],
                disease_id=diseases[r_info['disease_code']].id
            )
            for scode in r_info['symptom_codes']:
                r.symptoms.append(symptoms[scode])
            db.session.add(r)
            
        db.session.commit()
        print("Database seeded successfully with users, symptoms, diseases, and rules.")

if __name__ == '__main__':
    seed_database()
