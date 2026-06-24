from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Symptom, Disease, Rule, DiagnosisHistory
from functools import wraps
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Akses ditolak. Halaman ini hanya untuk administrator.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

# =========================================================================
# DASHBOARD
# =========================================================================
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_diseases = Disease.query.count()
    total_symptoms = Symptom.query.count()
    total_rules = Rule.query.count()
    total_diagnoses = DiagnosisHistory.query.count()
    
    # Recent diagnoses
    recent_diagnoses = DiagnosisHistory.query.order_by(DiagnosisHistory.created_at.desc()).limit(5).all()
    
    # Diagnosis distribution for Chart.js
    # Find count of each disease in diagnosis history
    all_diseases = Disease.query.all()
    disease_labels = []
    disease_counts = []
    
    # Add count for No Disease (Null)
    no_disease_count = DiagnosisHistory.query.filter_by(diagnosed_disease_id=None).count()
    
    for d in all_diseases:
        cnt = DiagnosisHistory.query.filter_by(diagnosed_disease_id=d.id).count()
        disease_labels.append(d.name)
        disease_counts.append(cnt)
        
    if no_disease_count > 0:
        disease_labels.append("Tidak Teridentifikasi")
        disease_counts.append(no_disease_count)
        
    # Chart Data as JSON
    chart_data = {
        'labels': disease_labels,
        'values': disease_counts
    }
    
    return render_template(
        'admin/dashboard.html',
        total_diseases=total_diseases,
        total_symptoms=total_symptoms,
        total_rules=total_rules,
        total_diagnoses=total_diagnoses,
        recent_diagnoses=recent_diagnoses,
        chart_data=json.dumps(chart_data)
    )

# =========================================================================
# DISEASE CRUD
# =========================================================================
@admin_bp.route('/diseases')
@login_required
@admin_required
def diseases():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Disease.query
    if search:
        query = query.filter(Disease.name.like(f"%{search}%") | Disease.code.like(f"%{search}%"))
        
    pagination = query.order_by(Disease.code.asc()).paginate(page=page, per_page=per_page)
    diseases_list = pagination.items
    
    return render_template('admin/diseases/list.html', diseases=diseases_list, pagination=pagination, search=search)

@admin_bp.route('/disease/add', methods=['GET', 'POST'])
@login_required
@admin_required
def disease_add():
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        description = request.form.get('description')
        causes = request.form.get('causes')
        treatment = request.form.get('treatment')
        prevention = request.form.get('prevention')
        
        # Check duplicate code
        if Disease.query.filter_by(code=code).first():
            flash(f"Kode penyakit '{code}' sudah digunakan.", 'danger')
            return redirect(url_for('admin.disease_add'))
            
        disease = Disease(
            code=code, name=name, description=description,
            causes=causes, treatment=treatment, prevention=prevention
        )
        db.session.add(disease)
        db.session.commit()
        
        flash(f"Penyakit '{name}' berhasil ditambahkan.", 'success')
        return redirect(url_for('admin.diseases'))
        
    # Auto-generate next code
    last = Disease.query.order_by(Disease.code.desc()).first()
    next_code = "P001"
    if last and last.code.startswith('P'):
        try:
            num = int(last.code[1:]) + 1
            next_code = f"P{num:03d}"
        except ValueError:
            pass
            
    return render_template('admin/diseases/form.html', action='Tambah', next_code=next_code)

@admin_bp.route('/disease/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def disease_edit(id):
    disease = Disease.query.get_or_404(id)
    if request.method == 'POST':
        disease.code = request.form.get('code')
        disease.name = request.form.get('name')
        disease.description = request.form.get('description')
        disease.causes = request.form.get('causes')
        disease.treatment = request.form.get('treatment')
        disease.prevention = request.form.get('prevention')
        
        # Validate unique code
        dup = Disease.query.filter(Disease.code == disease.code, Disease.id != id).first()
        if dup:
            flash(f"Kode penyakit '{disease.code}' sudah digunakan.", 'danger')
            return redirect(url_for('admin.disease_edit', id=id))
            
        db.session.commit()
        flash(f"Penyakit '{disease.name}' berhasil diperbarui.", 'success')
        return redirect(url_for('admin.diseases'))
        
    return render_template('admin/diseases/form.html', action='Ubah', disease=disease)

@admin_bp.route('/disease/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def disease_delete(id):
    disease = Disease.query.get_or_404(id)
    db.session.delete(disease)
    db.session.commit()
    flash(f"Penyakit '{disease.name}' berhasil dihapus.", 'success')
    return redirect(url_for('admin.diseases'))

# =========================================================================
# SYMPTOM CRUD
# =========================================================================
@admin_bp.route('/symptoms')
@login_required
@admin_required
def symptoms():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Symptom.query
    if search:
        query = query.filter(Symptom.name.like(f"%{search}%") | Symptom.code.like(f"%{search}%"))
        
    pagination = query.order_by(Symptom.code.asc()).paginate(page=page, per_page=per_page)
    symptoms_list = pagination.items
    
    return render_template('admin/symptoms/list.html', symptoms=symptoms_list, pagination=pagination, search=search)

@admin_bp.route('/symptom/add', methods=['GET', 'POST'])
@login_required
@admin_required
def symptom_add():
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        category = request.form.get('category')
        
        # Check duplicate code
        if Symptom.query.filter_by(code=code).first():
            flash(f"Kode gejala '{code}' sudah digunakan.", 'danger')
            return redirect(url_for('admin.symptom_add'))
            
        symptom = Symptom(code=code, name=name, category=category)
        db.session.add(symptom)
        db.session.commit()
        
        flash(f"Gejala '{name}' berhasil ditambahkan.", 'success')
        return redirect(url_for('admin.symptoms'))
        
    # Auto-generate next code
    last = Symptom.query.order_by(Symptom.code.desc()).first()
    next_code = "G001"
    if last and last.code.startswith('G'):
        try:
            num = int(last.code[1:]) + 1
            next_code = f"G{num:03d}"
        except ValueError:
            pass
            
    return render_template('admin/symptoms/form.html', action='Tambah', next_code=next_code)

@admin_bp.route('/symptom/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def symptom_edit(id):
    symptom = Symptom.query.get_or_404(id)
    if request.method == 'POST':
        symptom.code = request.form.get('code')
        symptom.name = request.form.get('name')
        symptom.category = request.form.get('category')
        
        # Validate unique code
        dup = Symptom.query.filter(Symptom.code == symptom.code, Symptom.id != id).first()
        if dup:
            flash(f"Kode gejala '{symptom.code}' sudah digunakan.", 'danger')
            return redirect(url_for('admin.symptom_edit', id=id))
            
        db.session.commit()
        flash(f"Gejala '{symptom.name}' berhasil diperbarui.", 'success')
        return redirect(url_for('admin.symptoms'))
        
    return render_template('admin/symptoms/form.html', action='Ubah', symptom=symptom)

@admin_bp.route('/symptom/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def symptom_delete(id):
    symptom = Symptom.query.get_or_404(id)
    db.session.delete(symptom)
    db.session.commit()
    flash(f"Gejala '{symptom.name}' berhasil dihapus.", 'success')
    return redirect(url_for('admin.symptoms'))

# =========================================================================
# RULE CRUD (Visual IF-THEN Builder)
# =========================================================================
@admin_bp.route('/rules')
@login_required
@admin_required
def rules():
    all_rules = Rule.query.order_by(Rule.code.asc()).all()
    return render_template('admin/rules/list.html', rules=all_rules)

@admin_bp.route('/rule/add', methods=['GET', 'POST'])
@login_required
@admin_required
def rule_add():
    if request.method == 'POST':
        code = request.form.get('code')
        disease_id = request.form.get('disease_id')
        selected_symptom_ids = request.form.getlist('symptoms')
        
        if not disease_id or not selected_symptom_ids:
            flash('Harap pilih penyakit kesimpulan dan minimal satu gejala aturan.', 'warning')
            return redirect(url_for('admin.rule_add'))
            
        # Check duplicate code
        if Rule.query.filter_by(code=code).first():
            flash(f"Kode aturan '{code}' sudah digunakan.", 'danger')
            return redirect(url_for('admin.rule_add'))
            
        rule = Rule(code=code, disease_id=int(disease_id))
        
        # Add symptoms
        for sid in selected_symptom_ids:
            sym = Symptom.query.get(int(sid))
            if sym:
                rule.symptoms.append(sym)
                
        db.session.add(rule)
        db.session.commit()
        
        flash(f"Aturan '{code}' berhasil ditambahkan.", 'success')
        return redirect(url_for('admin.rules'))
        
    # GET: Fetch diseases & symptoms for dropdowns/checkboxes
    diseases = Disease.query.order_by(Disease.name.asc()).all()
    symptoms = Symptom.query.order_by(Symptom.code.asc()).all()
    
    # Auto-generate next code
    last = Rule.query.order_by(Rule.code.desc()).first()
    next_code = "R001"
    if last and last.code.startswith('R'):
        try:
            num = int(last.code[1:]) + 1
            next_code = f"R{num:03d}"
        except ValueError:
            pass
            
    return render_template('admin/rules/form.html', action='Tambah', next_code=next_code, diseases=diseases, symptoms=symptoms)

@admin_bp.route('/rule/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def rule_edit(id):
    rule = Rule.query.get_or_404(id)
    if request.method == 'POST':
        rule.code = request.form.get('code')
        rule.disease_id = int(request.form.get('disease_id'))
        selected_symptom_ids = request.form.getlist('symptoms')
        
        if not selected_symptom_ids:
            flash('Harap pilih minimal satu gejala aturan.', 'warning')
            return redirect(url_for('admin.rule_edit', id=id))
            
        # Check duplicate code
        dup = Rule.query.filter(Rule.code == rule.code, Rule.id != id).first()
        if dup:
            flash(f"Kode aturan '{rule.code}' sudah digunakan.", 'danger')
            return redirect(url_for('admin.rule_edit', id=id))
            
        # Clear old symptoms and add new ones
        rule.symptoms.clear()
        for sid in selected_symptom_ids:
            sym = Symptom.query.get(int(sid))
            if sym:
                rule.symptoms.append(sym)
                
        db.session.commit()
        flash(f"Aturan '{rule.code}' berhasil diperbarui.", 'success')
        return redirect(url_for('admin.rules'))
        
    diseases = Disease.query.order_by(Disease.name.asc()).all()
    symptoms = Symptom.query.order_by(Symptom.code.asc()).all()
    rule_symptom_ids = [s.id for s in rule.symptoms]
    
    return render_template(
        'admin/rules/form.html',
        action='Ubah',
        rule=rule,
        diseases=diseases,
        symptoms=symptoms,
        rule_symptom_ids=rule_symptom_ids
    )

@admin_bp.route('/rule/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def rule_delete(id):
    rule = Rule.query.get_or_404(id)
    db.session.delete(rule)
    db.session.commit()
    flash(f"Aturan '{rule.code}' berhasil dihapus.", 'success')
    return redirect(url_for('admin.rules'))

# =========================================================================
# USER MANAGEMENT
# =========================================================================
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.role.asc(), User.username.asc()).all()
    return render_template('admin/users/list.html', users=all_users)

@admin_bp.route('/user/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def user_edit(id):
    user = User.query.get_or_404(id)
    
    # Prevent admin from changing their own role/status
    if user.id == current_user.id:
        flash('Anda tidak dapat mengubah peran atau status akun Anda sendiri.', 'warning')
        return redirect(url_for('admin.users'))
        
    new_role = request.form.get('role')
    new_status = request.form.get('status')
    
    if new_role in ['admin', 'patient']:
        user.role = new_role
    if new_status in ['active', 'inactive']:
        user.status = new_status
        
    db.session.commit()
    flash(f"Data pengguna '{user.username}' berhasil diperbarui.", 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('Anda tidak dapat menghapus akun Anda sendiri.', 'danger')
        return redirect(url_for('admin.users'))
        
    db.session.delete(user)
    db.session.commit()
    flash(f"Pengguna '{user.username}' berhasil dihapus.", 'success')
    return redirect(url_for('admin.users'))
