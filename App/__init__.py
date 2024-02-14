from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
# from flask_multipass import Multipass, IdentityProvider

socketio = SocketIO(cors_allowed_origins="*")
db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin(name='admin')
# multipass = Multipass()

DB_NAME = 'sahabatBacarita.db'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sr_SahabatBacarita'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # app.config['FLASK_ADMIN_SWATCH'] = 'simplex'
    db.init_app(app)
    admin.init_app(app)
    socketio.init_app(app)

    # multipass.init_app(app)
    login_manager.init_app(app)

    from .auth.routes import auth
    from .views.routes import views

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    login_manager.login_view = 'auth.login'

    # from web import models
    from .models import SuperSU

    with app.app_context():
        db.create_all()

        if not SuperSU.query.first():
            supersu = SuperSU(username='admin', password=generate_password_hash('admsarita123', method='pbkdf2'))
            db.session.add(supersu)
            db.session.commit()

    return app
