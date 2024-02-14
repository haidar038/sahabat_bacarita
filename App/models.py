from App import db, admin
from flask_login import UserMixin
from datetime import datetime
from flask_admin.contrib.sqla.view import ModelView
from flask_admin.base import BaseView, expose
# from flask_admin.contrib.sqla import ModelView
# from flask_admin.menu import MenuLink
# from flask_login import current_user

now = datetime.now()

# class Admin(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    room_id = db.Column(db.String, nullable=False)
    account_type = db.Column(db.String, nullable=False, default='user')
    cerita = db.relationship('Cerita', backref='user', lazy=True)
    chat = db.relationship('Chat', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.nama_lengkap}','{self.email}','{self.username}')"
    
class SuperSU(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    account_type = db.Column(db.String(80), nullable=False, default='admin')

    def __repr__(self):
        return f"SuperSU('{self.username}')"

class Cerita(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    konten = db.Column(db.String, nullable=False)
    tanggal = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean, default=False, nullable=False)
    anonym = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def get_status_text(self):
        return "Active" if self.status else "Inactive"

class Chat(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    pesan = db.Column(db.String, nullable=False)
    tanggal = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    room_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
