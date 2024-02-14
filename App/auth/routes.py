from flask import Blueprint, request, render_template, flash, redirect, url_for, session, Response
from flask_login import login_required, logout_user, login_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from string import ascii_uppercase

from App.models import User, SuperSU, Chat
from App import db, login_manager, fernet

import random

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(id):
    if 'account_type' in session:
        if session['account_type'] == 'admin':
            return SuperSU.query.get(int(id))
        elif session['account_type'] == 'user':
            return User.query.get(int(id))
    else:
        return None

@auth.route('/adminLogin', methods=['GET', 'POST'])
def adminLogin():
    if current_user.is_authenticated:
        if current_user.account_type == 'admin':
            return redirect(url_for('views.dashboard'))
        elif current_user.account_type == 'user':
            return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['userPassword']
        
        admin_user = SuperSU.query.filter_by(username=username).first()

        if admin_user and check_password_hash(admin_user.password, password):
            session['account_type'] = 'admin'
            print("Anda berhasil masuk!")
            flash("Anda berhasil masuk!", category="success")
            login_user(admin_user, remember=True)
            return redirect(url_for('views.dashboard'))
        elif admin_user is None:
            print(f"Akun dengan username {username} tidak ditemukan. Mungkin anda telah menggantinya!")
            flash(f"Akun dengan username {username} tidak ditemukan. Mungkin anda telah menggantinya!", category='warning')
            return redirect(url_for('auth.adminLogin'))
        else:
            print("Kata sandi salah, coba lagi.")
            flash("Kata sandi salah, coba lagi.", category='danger')
            return redirect(url_for('auth.adminLogin'))

    return render_template('admin_login.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.account_type == 'admin':
            return redirect(url_for('views.dashboard'))
        elif current_user.account_type == 'user':
            return redirect(url_for('views.home'))
    if request.method == 'POST':
        email = request.form['emailAddress']
        password = request.form['userPassword']
        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['account_type'] = 'user'
            flash("Berhasil Masuk!", category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
        elif user is None:
            flash("Akun anda belum terdaftar, silakan daftar terlebih dahulu", category='warning')
        else:
            flash("Kata sandi salah, silakan coba lagi.", category='danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html', page='User')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.account_type == 'admin':
            return redirect(url_for('views.dashboard'))
        elif current_user.account_type == 'user':
            return redirect(url_for('views.home'))
    if request.method == 'POST':
        full_name = request.form['nama']
        username = request.form['userName']
        email = request.form['emailAddress']
        password = request.form['userPassword']
        confirm_password = request.form['confirmUserPassword']

        if len(password) < 8:
            flash('Kata sandi harus berisi 8 karakter atau lebih', category='danger')
        elif confirm_password != password:
            flash('Kata sandi tidak cocok.', category='danger')
        elif User.query.filter_by(username=username).first():
            flash('Nama pengguna sudah digunakan, silakan buat yang lain.', category='danger')
        else:
            room_id = ''
            for _ in range(8):
                room_id += random.choice(ascii_uppercase)
            if room_id not in User.query.values(User.room_id):
                add_User = User(nama_lengkap=full_name, email=email, username=username, room_id=room_id, password=generate_password_hash(password, method='pbkdf2'))
                db.session.add(add_User)
                db.session.commit()
                flash('Akun berhasil dibuat!', category='success')
                return redirect(url_for('auth.login'))

    return render_template('register.html', page='User')

@auth.route('/logout')
@login_required
def logout():
    if session['account_type'] == 'admin':
        flash('You have logged out!', 'warning')
        logout_user()
        session.clear()
        return redirect(url_for('auth.adminLogin'))
    elif session['account_type'] == 'user':
        flash('You have logged out!', 'warning')
        logout_user()
        session.clear()
        return redirect(url_for('auth.login'))

@auth.route("/abort")
def abort():
    return Response(response="Unauthorized", status=401)