from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify, session
from flask_login import login_required, logout_user, login_user, current_user
from flask_admin.base import BaseView, expose, AdminIndexView, Admin
from flask_socketio import emit, join_room, leave_room, send, rooms
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from App.models import User, Cerita, Chat, SuperSU
from App import db, admin, login_manager, socketio, fernet

views = Blueprint('views', __name__)

@views.route('/', methods=['POST', 'GET'])
def index():
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
            flash(f"Akun dengan email {email} tidak ditemukan. Silakan daftar terlebih dahulu!",'warning')
            return redirect(url_for('auth.login'))
        else:
            flash("Kata sandi salah, coba lagi.", 'error')
            return redirect(url_for('auth.login'))
    return render_template('index.html')

@views.route('/beranda', methods=['GET', 'POST'])
@login_required
def home():
    if current_user.is_authenticated and session['account_type'] == 'user':
        postingan = Cerita.query.all()
        user = User.query.all()

        if request.method == 'POST':
            teks = request.form['tulisan']
            anonym = True if request.form.get('anonim') == 'on' else False

            cerita = Cerita(konten=teks, tanggal=datetime.utcnow(), status=False, anonym=anonym, user_id=current_user.id)
            db.session.add(cerita)
            db.session.commit()
            print('Cerita berhasil dibuat!')
            return redirect(request.referrer)
        return render_template('beranda.html', postingan=postingan, user=user)
    elif current_user.is_authenticated and session['account_type'] == 'admin':
        return redirect(url_for('views.dashboard'))
    else:
        return redirect(url_for('auth.login'))
    
@views.route('/profil/<string:username>', methods=['GET', 'POST'])
@login_required
def profil(username):
    if current_user.is_authenticated and session['account_type'] == 'user':
        # user = User.query.filter_by(username=username)
        user = User.query.filter_by(username=username).first()

        if request.method == 'POST':
            if user:
                password = request.form['password']
                if check_password_hash(user.password, password):
                    # update_user = User(nama_lengkap=full_name, email=email,
                    #                   username=username, password=generate_password_hash(password, method='pbkdf2'),
                    #                   room_id=user.room_id, cerita=user.cerita, chat=user.chat)

                    # db.session.delete(user)
                    # db.session.add(update_user)
                    user.nama_lengkap = request.form['nama_lengkap']
                    user.username = request.form['username']
                    user.email = request.form['email']
                    user.password = generate_password_hash(request.form['password'], method='pbkdf2')
                    db.session.commit()
                    flash('Akun berhasil diubah!', category='success')
                    print('Akun berhasil diperbarui!')
                    return redirect(url_for('views.profil', username=username))
                else:
                    flash("Kata sandi salah, silakan coba lagi.", category='danger')
                    return redirect(url_for('views.profil', username=user.username))

        post = Cerita.query.filter_by(user_id=current_user.id).all()
        return render_template("profil.html", user=user, post=post)

        # ... other code for admin and unauthorized access


    elif current_user.is_authenticated and session['account_type'] == 'admin':
        return render_template("admin_profile.html")
    else:
        return redirect(url_for('auth.login'))

@views.route('/about')
def about():
    return render_template('about.html')


# +++++++++++++++++++++++++++++++++++++ CHAT ROOM SESSION ++++++++++++++++++++++++++++++++++++++++

# page = request.args.get('page', 1, type=int)
# per_page = 10  # Ubah sesuai kebutuhan
# messages = Chat.query.filter_by(room_id=room).order_by(Chat.timestamp.desc()).paginate(page, per_page, error_out=False)
# chatContent = messages.items

@views.route('/chat/<string:room>/', defaults={'page_num': 1})
@views.route('/chat/<string:room>/<int:page_num>')
@login_required
def chat(room, page_num):
    user = User.query.all()
    superuser = SuperSU.query.filter_by(account_type='admin').first()
    if user or superuser:
        msgs = Chat.query.filter_by(room_id=room).order_by(Chat.tanggal.desc()).paginate(page=page_num, per_page=5)
        return render_template('chat_room.html', room=room, user=user, msgs=msgs, error_out=True)
    else:
        return "User not found", 404

# @views.route('/get_messages', methods=['GET'])
# def get_messages():
#     page = request.args.get('page', 1, type=int)
#     per_page = 10  # Ubah sesuai kebutuhan

#     messages = Chat.query.order_by(Chat.timestamp.desc()).paginate(page, per_page, error_out=False)
#     messages_data = [{'content': msg.content, 'user_id': msg.user_id} for msg in messages.items]

#     return jsonify({'messages': messages_data, 'has_next': messages.has_next})

@views.route('/chat/delete_chat/<string:room>', methods=['GET'])
def delete_chat(room):
    # Use the SQLAlchemy delete() method to delete all rows
    chat = Chat.query.filter_by(room_id=room).all()
    for chats in chat:
        db.session.delete(chats)
    
    # Commit the changes to the database
    db.session.commit()

    return redirect(request.referrer)

@socketio.on("connect")
def connect():
    print("Client connected!")

@socketio.on('online')
def online(data):
    emit('status_change', {'username': data['username'], 'status': 'online'}, broadcast=True)

@socketio.on("user_join")
def user_join(room):
    username = current_user.username
    join_room(room)
    if session['account_type'] == 'admin':
        chats = Chat.query.filter_by(room_id=room).all()
        for chat in chats:
            chat.read = True
        db.session.commit()
    emit('join', {'username':username}, to=room)
    print(f"Client {username} joined to {room}!")

@socketio.on("new_message")
def handle_message(message, room):
    username = current_user.username
    if room in rooms():
        emit('chat', {'username':username, 'message':message}, broadcast=True, to=room)

    print(f"New message: {message} from {username}")
    msg_content = Chat(pesan=message, tanggal=datetime.utcnow(), sender=current_user.username, room_id=room, user_id=current_user.id)
    db.session.add(msg_content)
    db.session.commit()

@socketio.on('leave')
def leave(room):
    username = current_user.username
    room = room
    print(f"{username} leave room")
    leave_room(room)
    emit('leave', {'username': username}, to=room)

# +++++++++++++++++++++++++++++++ CHAT ROOM SESSION ++++++++++++++++++++++++++=


# todo =========================== ADMIN SECTION =================================
@views.route('/adminProfile/<string:username>', methods=['GET', 'POST'])
@login_required
def adminProfile(username):
    if current_user.is_authenticated and current_user.account_type == 'admin':
        user = SuperSU.query.filter_by(username=username).first()

        if request.method == 'POST':
            if user:
                db.session.delete(user)
                db.session.commit()
                username = request.form['username']
                password = request.form['password']

                if check_password_hash(user.password, password):
                    update_user = SuperSU(username=username, password=generate_password_hash(password, method='pbkdf2'))
                    db.session.add(update_user)
                    db.session.commit()
                    flash('Akun berhasil diubah!', category='success')
                    print('Akun berhasil diperbarui!')
                    return redirect(url_for('views.adminProfile', username=username))
        return render_template("admin_profile.html")
    
    elif current_user.is_authenticated and current_user.account_type == 'user':
        return render_template("profil.html")
    else:
        return redirect(url_for('auth.adminlogin'))

@views.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.is_authenticated and current_user.account_type == 'admin':
        user_data = User.query.all()
        cerita = Cerita.query.all()
        chat = Chat.query.filter_by(read=False).all()
        chat_counts = {user.room_id: sum(1 for chats in chat if chats.room_id == user.room_id and chats.read == False) for user in user_data}
        return render_template('dashboard.html', user_data=user_data, cerita=cerita, chat=chat, chat_counts=chat_counts)
    elif current_user.is_authenticated and current_user.account_type == 'user':
        return redirect(url_for('views.home'))
        
    else:
        return redirect(url_for('auth.login'))


@views.route('/dashboard/approve_post/<int:id>', methods=['GET'])
def approve_post(id):
    post = Cerita.query.get_or_404(id)
    post.status = True
    db.session.commit()
    return redirect(url_for('views.dashboard'))

@views.route('/delete_post/<int:id>', methods=['GET'])
def delete_post(id):
    post = Cerita.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('views.dashboard'))

@views.route('/dashboard/delete_user/<int:id>', methods=['GET'])
def delete_user(id):
    users = User.query.get_or_404(id)
    db.session.delete(users)
    db.session.commit()
    return redirect(url_for('views.dashboard'))

# todo ============== UPDATE PROFILE ==============
# @views.route('/dashboard/<int:id>/update', methods=['GET', 'POST'])
# @login_required
# def update_profile(id):
#     user = User.query.filter_by(id=id).first()

#     if request.method == 'POST':
#         if user:
#             db.session.delete(user)
#             db.session.commit()
#             full_name = request.form['full_name']
#             username = request.form['username']
#             student_id = request.form['student_id']
#             grade = request.form['grade']
#             address = request.form['address']
#             region_group = request.form['region_group']
#             subdistrict = request.form['subdistrict']
#             district = request.form['district']
#             province = request.form['province']
#             zipcode = request.form['zipcode']
#             parents = request.form['parents']
#             phone = request.form['phone']
#             best_friend = request.form['best_friend']
#             ambition = request.form['ambition']
#             motto = request.form['motto']
#             disease = request.form['disease']
#             password = request.form['password']   
            
#             user = User(full_name=full_name, username=username, student_id=student_id, grade=grade, address=address, region_group=region_group, subdistrict=subdistrict, district=district, province=province, zipcode=zipcode, parents=parents, phone=phone, best_friend=best_friend, ambition=ambition, motto=motto, disease=disease, password=user.password)
            
#             db.session.add(user)
#             db.session.commit()
#             flash('Profile Updated!', category='success')
#             return redirect(url_for('views.dashboard'))
        
#         return f"Student with id = {id} Does not exist"

#     return render_template('update_profile.html', user=user)

# @views.route('/dashboard/<int:id>/change_password', methods=['GET', 'POST'])
# def change_pass():
#     passd = Student.query.filter_by(password=current_user.password).first()
#     if request.method == 'POST':
#         if

class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        user = User.query.all()
        return self.render('admin/index.html', user=user)

admin = Admin(index_view=MyHomeView())