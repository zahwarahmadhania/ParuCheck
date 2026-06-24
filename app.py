import os
from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager
from config import Config
from models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize DB
    db.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.login_message = 'Silakan masuk terlebih dahulu untuk mengakses halaman ini.'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register Blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Ensure database exists and seed if empty
    with app.app_context():
        db.create_all()
        # Seed logic inline to auto-initialize on launch
        if not User.query.filter_by(role='admin').first():
            print("Auto-seeding database...")
            try:
                from seed import seed_database
                seed_database()
            except Exception as e:
                print(f"Error seeding database: {e}")
                
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)