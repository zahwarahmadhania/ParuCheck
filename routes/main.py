from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session
from flask_login import current_user, login_required
from models import db, Symptom, Disease, Rule, DiagnosisHistory
from utils.engine import run_forward_chaining
import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Fetch some counts for the visual diagrams
    symptoms_count = Symptom.query.count()
    diseases_count = Disease.query.count()
    rules_count = Rule.query.count()
    return render_template('main/home.html', symptoms_count=symptoms_count, diseases_count=diseases_count, rules_count=rules_count)

@main_bp.route('/consultation', methods=['GET', 'POST'])
def consultation():
    if request.method == 'POST':
        # Get patient details
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        patient_gender = request.form.get('patient_gender')
        
        # Get selected symptoms
        selected_symptoms = request.form.getlist('symptoms')
        
        # Validation
        if not patient_name or not patient_age or not patient_gender:
            flash('Harap lengkapi semua data diri pasien.', 'warning')
            return redirect(url_for('main.consultation'))
            
        if not selected_symptoms:
            flash('Harap pilih minimal satu gejala yang dirasakan.', 'warning')
            return redirect(url_for('main.consultation'))
            
        # Run inference engine
        symptom_ids = [int(sid) for sid in selected_symptoms]
        diagnosis_res = run_forward_chaining(symptom_ids)
        
        # Get resolved primary disease ID
        primary_disease_id = None
        if diagnosis_res['primary_diagnosis']:
            primary_disease_id = diagnosis_res['primary_diagnosis'].id
            
        confidence = diagnosis_res['confidence']
        
        # Resolve symptoms details to store in JSON
        symptom_objects = Symptom.query.filter(Symptom.id.in_(symptom_ids)).all()
        symptoms_list_data = [{'code': s.code, 'name': s.name} for s in symptom_objects]
        
        # Save to DB
        user_id = current_user.id if current_user.is_authenticated else None
        history = DiagnosisHistory(
            user_id=user_id,
            patient_name=patient_name,
            patient_age=int(patient_age),
            patient_gender=patient_gender,
            confidence_percentage=confidence,
            diagnosed_disease_id=primary_disease_id
        )
        history.symptoms_list = symptoms_list_data
        
        db.session.add(history)
        db.session.commit()
        
        # Save guest history to session so guest can view result
        if not current_user.is_authenticated:
            session[f"guest_diagnosis_{history.id}"] = True
            
        return redirect(url_for('main.result', history_id=history.id))
        
    # GET: fetch all symptoms grouped by category
    symptoms = Symptom.query.all()
    grouped_symptoms = {}
    for sym in symptoms:
        cat = sym.category or 'Umum'
        if cat not in grouped_symptoms:
            grouped_symptoms[cat] = []
        grouped_symptoms[cat].append(sym)
        
    return render_template('main/consultation.html', grouped_symptoms=grouped_symptoms)

@main_bp.route('/result/<int:history_id>')
def result(history_id):
    history = DiagnosisHistory.query.get_or_404(history_id)
    
    # Check authorization (if logged in, check owner; if guest, check session token)
    if history.user_id:
        if not current_user.is_authenticated or (current_user.id != history.user_id and current_user.role != 'admin'):
            flash('Anda tidak memiliki akses untuk melihat hasil ini.', 'danger')
            return redirect(url_for('main.home'))
    else:
        # It's a guest result
        if not session.get(f"guest_diagnosis_{history_id}") and (not current_user.is_authenticated or current_user.role != 'admin'):
            flash('Anda tidak memiliki akses untuk melihat hasil ini.', 'danger')
            return redirect(url_for('main.home'))
            
    # Re-run engine logic to get details (triggered rules & differentials)
    # This is cleaner than storing all engine internals in the database
    symptom_names = [s['name'] for s in history.symptoms_list]
    db_symptoms = Symptom.query.filter(Symptom.name.in_(symptom_names)).all()
    symptom_ids = [s.id for s in db_symptoms]
    
    diagnosis_res = run_forward_chaining(symptom_ids)
    
    return render_template(
        'main/result.html',
        history=history,
        primary_disease=history.disease,
        confidence=history.confidence_percentage,
        triggered_rules=diagnosis_res['triggered_rules'],
        differential_diagnoses=diagnosis_res['differential_diagnoses']
    )

@main_bp.route('/result/<int:history_id>/pdf')
def result_pdf(history_id):
    history = DiagnosisHistory.query.get_or_404(history_id)
    
    # Authorization checks
    if history.user_id:
        if not current_user.is_authenticated or (current_user.id != history.user_id and current_user.role != 'admin'):
            flash('Akses ditolak.', 'danger')
            return redirect(url_for('main.home'))
    else:
        if not session.get(f"guest_diagnosis_{history_id}") and (not current_user.is_authenticated or current_user.role != 'admin'):
            flash('Akses ditolak.', 'danger')
            return redirect(url_for('main.home'))

    # Generate PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # PDF Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#0EA5E9'),
        spaceAfter=15
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        leading=14
    )
    bold_body_style = ParagraphStyle(
        'BoldBodyTextCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    # Title
    story.append(Paragraph("PARUCHECK - LAPORAN DIAGNOSTIK MEDIS", title_style))
    story.append(Paragraph("Sistem Pakar Deteksi Dini Penyakit Paru-Paru (Forward Chaining)", body_style))
    story.append(Spacer(1, 15))
    
    # Patient Data Table
    patient_data = [
        [Paragraph("Informasi Pasien", section_title), ""],
        [Paragraph("Nama Pasien:", bold_body_style), Paragraph(history.patient_name, body_style)],
        [Paragraph("Umur Pasien:", bold_body_style), Paragraph(f"{history.patient_age} Tahun", body_style)],
        [Paragraph("Jenis Kelamin:", bold_body_style), Paragraph("Laki-laki" if history.patient_gender == 'L' else "Perempuan", body_style)],
        [Paragraph("Tanggal Konsultasi:", bold_body_style), Paragraph(history.created_at.strftime('%d %B %Y - %H:%M:%S'), body_style)]
    ]
    t1 = Table(patient_data, colWidths=[130, 370])
    t1.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('LINEBELOW', (0, 0), (1, 0), 1.5, colors.HexColor('#0EA5E9')),
        ('BOTTOMPADDING', (0, 0), (1, 0), 5),
        ('TOPPADDING', (0, 1), (1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (1, -1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))
    
    # Selected Symptoms Table
    symptom_rows = [[Paragraph("Gejala yang Dipilih oleh Pasien", section_title)]]
    for s in history.symptoms_list:
        symptom_rows.append([Paragraph(f"• [{s['code']}] {s['name']}", body_style)])
        
    t2 = Table(symptom_rows, colWidths=[500])
    t2.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 1.5, colors.HexColor('#0EA5E9')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 5),
        ('TOPPADDING', (0, 1), (0, -1), 3),
        ('BOTTOMPADDING', (0, 1), (0, -1), 3),
    ]))
    story.append(t2)
    story.append(Spacer(1, 15))
    
    # Diagnosis Result Table
    disease = history.disease
    disease_name = disease.name if disease else "Tidak Teridentifikasi / Gejala Tidak Spesifik"
    confidence = f"{history.confidence_percentage}%"
    
    desc_val = disease.description if disease else "Sistem tidak mendeteksi kecocokan gejala dengan aturan penyakit paru yang terdaftar. Silakan lakukan konsultasi ulang atau periksa ke dokter spesialis paru terdekat."
    causes_val = disease.causes if disease else "-"
    treat_val = disease.treatment if disease else "-"
    prev_val = disease.prevention if disease else "-"
    
    result_data = [
        [Paragraph("Hasil Analisis Sistem Pakar", section_title), ""],
        [Paragraph("Diagnosis Utama:", bold_body_style), Paragraph(disease_name, ParagraphStyle('DName', parent=bold_body_style, textColor=colors.HexColor('#EF4444')))],
        [Paragraph("Tingkat Keyakinan (Confidence):", bold_body_style), Paragraph(confidence, ParagraphStyle('Conf', parent=bold_body_style, textColor=colors.HexColor('#22C55E')))],
        [Paragraph("Deskripsi Penyakit:", bold_body_style), Paragraph(desc_val, body_style)],
        [Paragraph("Penyebab Umum:", bold_body_style), Paragraph(causes_val, body_style)],
        [Paragraph("Rekomendasi Pengobatan:", bold_body_style), Paragraph(treat_val, body_style)],
        [Paragraph("Langkah Pencegahan:", bold_body_style), Paragraph(prev_val, body_style)]
    ]
    
    t3 = Table(result_data, colWidths=[150, 350])
    t3.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('LINEBELOW', (0, 0), (1, 0), 1.5, colors.HexColor('#0EA5E9')),
        ('BOTTOMPADDING', (0, 0), (1, 0), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (1, -1), 6),
    ]))
    story.append(t3)
    
    story.append(Spacer(1, 30))
    story.append(Paragraph("Catatan: Laporan ini dihasilkan secara otomatis oleh expert system ParuCheck berdasarkan data gejala yang dimasukkan oleh pasien. Hasil ini ditujukan sebagai skrining awal dan tidak menggantikan diagnosis medis profesional dari dokter.", ParagraphStyle('Note', parent=body_style, fontSize=8, textColor=colors.HexColor('#64748B'), leading=10)))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"Laporan_ParuCheck_{history.patient_name.replace(' ', '_')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@main_bp.route('/diseases')
def diseases():
    search = request.args.get('search', '')
    if search:
        all_diseases = Disease.query.filter(Disease.name.like(f"%{search}%") | Disease.description.like(f"%{search}%")).all()
    else:
        all_diseases = Disease.query.all()
        
    # For visual display, let's map each disease code to symptoms list from rule base
    diseases_with_symptoms = []
    for d in all_diseases:
        # Find symptoms from rules matching this disease
        rule = Rule.query.filter_by(disease_id=d.id).first()
        symptoms_list = rule.symptoms if rule else []
        diseases_with_symptoms.append({
            'disease': d,
            'symptoms': symptoms_list
        })
        
    return render_template('main/diseases.html', diseases=diseases_with_symptoms, search=search)

@main_bp.route('/history')
def history():
    # Only show history if logged in. Guests don't have a history log, but let's tell them to log in.
    if not current_user.is_authenticated:
        flash('Silakan masuk terlebih dahulu untuk melihat riwayat konsultasi Anda.', 'warning')
        return redirect(url_for('auth.login'))
        
    # Admin can see all history; Patient only sees their own
    query = DiagnosisHistory.query
    if current_user.role != 'admin':
        query = query.filter_by(user_id=current_user.id)
        
    # Search and Filter
    search = request.args.get('search', '')
    gender = request.args.get('gender', '')
    disease_id = request.args.get('disease_id', '')
    
    if search:
        query = query.filter(DiagnosisHistory.patient_name.like(f"%{search}%"))
    if gender:
        query = query.filter(DiagnosisHistory.patient_gender == gender)
    if disease_id:
        query = query.filter(DiagnosisHistory.diagnosed_disease_id == int(disease_id))
        
    histories = query.order_by(DiagnosisHistory.created_at.desc()).all()
    all_diseases = Disease.query.all()
    
    return render_template('main/history.html', histories=histories, diseases=all_diseases, search=search, gender=gender, disease_id=disease_id)
