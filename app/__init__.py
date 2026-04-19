"""Flask Application Factory for Boston AI Life Sciences ERP System."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://erp_user:erp_password@localhost:5432/erp_database'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    CORS(app)

    # User loader for Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.modules.procurement import procurement_bp
    from app.modules.goods_receiving import goods_receiving_bp
    from app.modules.production import production_bp
    from app.modules.packaging import packaging_bp
    from app.modules.sales import sales_bp
    from app.modules.financial import financial_bp
    from app.modules.reporting import reporting_bp
    from app.modules.auth import auth_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(procurement_bp, url_prefix='/procurement')
    app.register_blueprint(goods_receiving_bp, url_prefix='/goods-receiving')
    app.register_blueprint(production_bp, url_prefix='/production')
    app.register_blueprint(packaging_bp, url_prefix='/packaging')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(financial_bp, url_prefix='/financial')
    app.register_blueprint(reporting_bp, url_prefix='/reporting')

    # Create tables
    with app.app_context():
        db.create_all()

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'Boston AI Life Sciences ERP'}

    return app
