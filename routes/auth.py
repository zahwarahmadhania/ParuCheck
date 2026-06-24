from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Username atau password salah. Silakan coba lagi.', 'danger')
            return redirect(url_for('auth.login'))
            
        if user.status != 'active':
            flash('Akun Anda dinonaktifkan. Silakan hubungi admin.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        
        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.home'))
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if password matches
        if password != confirm_password:
            flash('Konfirmasi kata sandi tidak cocok.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if username exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username sudah digunakan.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if email exists
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('Email sudah terdaftar.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new patient user
        new_user = User(
            username=username,
            email=email,
            role='patient',
            status='active'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan masuk.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah keluar dari akun.', 'success')
    return redirect(url_for('main.home'))
