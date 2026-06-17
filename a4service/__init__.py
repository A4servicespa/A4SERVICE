from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail

# Importar configuración correcta
from a4service.config import Config

# ============================
# INSTANCIAS GLOBALES
# ============================
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # ============================
    # CARGAR CONFIGURACIÓN DESDE config.py
    # ============================
    app.config.from_object(Config)

    # ============================
    # CONFIGURACIÓN DE CORREO (OUTLOOK)
    # ============================
    app.config["MAIL_SERVER"] = "smtp.office365.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "TU_CORREO_OUTLOOK"   # <-- CAMBIAR
    app.config["MAIL_PASSWORD"] = "TU_PASSWORD_OUTLOOK" # <-- CAMBIAR
    app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

    # CORS
    CORS(app)

    # ============================
    # INICIALIZAR EXTENSIONES
    # ============================
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # LOGIN
    login_manager.login_view = "auth.login"

    from a4service.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # ============================
    # IMPORTAR BLUEPRINTS
    # ============================
    from a4service.routes.auth import auth_bp
    from a4service.routes.dashboard import dashboard_bp
    from a4service.routes.clientes import clientes_bp
    from a4service.routes.productos import productos_bp
    from a4service.routes.cotizaciones import cotizaciones_bp
    from a4service.routes.facturas import facturas_bp
    from a4service.routes.movimientos import movimientos_bp
    from a4service.routes.facturas_archivo import facturas_archivo_bp
    from a4service.routes.costos import costos_bp
    from a4service.routes.insumos import insumos_bp
    from a4service.routes.categorias_insumo import categorias_insumo_bp

    # ============================
    # REGISTRO DE BLUEPRINTS
    # ============================
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(cotizaciones_bp)
    app.register_blueprint(facturas_bp)
    app.register_blueprint(movimientos_bp)
    app.register_blueprint(facturas_archivo_bp)
    app.register_blueprint(costos_bp)
    app.register_blueprint(insumos_bp)
    app.register_blueprint(categorias_insumo_bp)

    # ============================
    # RUTA PRINCIPAL
    # ============================
    @app.route("/")
    def home():
        return redirect(url_for("dashboard.dashboard"))

    # ============================
    # CREAR TABLAS SI NO EXISTEN
    # ============================
    with app.app_context():
        db.create_all()

    return app
