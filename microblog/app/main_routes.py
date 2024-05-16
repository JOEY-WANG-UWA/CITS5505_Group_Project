from flask import Blueprint, render_template, flash, redirect, url_for,g,request, current_app, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from sqlalchemy import select, func, or_, distinct

from datetime import datetime, timezone
from collections import defaultdict

from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm,EmptyForm, ResetPasswordRequestForm, ResetPasswordForm, SearchForm, MessageForm, UploadForm,CommentForm
from app.models import User, Post, Message, Notification, Upload, Upload_detail, Comment, Collection, Favourite, followers


main_bp = Blueprint('main_bp', __name__)

def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

@main_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()



def fetch_data_gallery():
    # Fetch all necessary data from the database
    uploads_with_collection = db.session.query(
        Upload.id,
        Upload.title,
        User.username,
        User.avatar,
        Upload.description,
        func.count(distinct(Collection.id)).label('collect_count'),
        func.count(distinct(Comment.id)).label('comment_count')
    ).select_from(Upload).join(User).outerjoin(Collection, Collection.upload_id == Upload.id)\
        .outerjoin(Comment, Comment.upload_id == Upload.id)\
        .group_by(Upload.id, Upload.title, User.username)\
        .all()

    grouped_details = defaultdict(dict)
    for upload_id, title, username, avatar, description, collect_count, comment_count in uploads_with_collection:
        grouped_details[upload_id] = {
            'title': title,
            'username': username,
            'avatar': avatar,
            'description': description,
            'collect_count': collect_count,
            'comment_count': comment_count,
            'items': []
        }

    uploads = Upload.query.all()
    for upload in uploads:
        for detail in upload.updetails:
            grouped_details[upload.id]['items'].append(detail.upload_item)

    return grouped_details

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def gallery():
    uploads = Upload.query.all()
    grouped_details = fetch_data_gallery()
    for upload in uploads:
        for detail in upload.updetails:
            grouped_details[upload.id].append(detail)
    return render_template('main/gallery_view.html', grouped_details=grouped_details)

@main_bp.route('/explore', methods=['GET', 'POST'])
def explore():
    uploads = Upload.query.order_by(Upload.upload_time.desc()).all()
    return redirect(url_for('main.gallery'))

@main_bp.route('/add_to_collection/<int:upload_id>', methods=['POST'])
@login_required
def add_to_collection(upload_id):
    upload = db.get_or_404(Upload, upload_id)
    collection = Collection(user_id=current_user.id, upload_id=upload.id)
    db.session.add(collection)
    db.session.commit()
    flash('Upload added to collection.')
    return redirect(url_for('main.gallery'))

@main_bp.route('/post_comment/<int:upload_id>', methods=['POST'])
@login_required
def post_comment(upload_id):
    upload = db.get_or_404(Upload, upload_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, upload=upload)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.')
    return redirect(url_for('main.show_photo', photo_id=upload.id))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.gallery'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.gallery'))
    return render_template('login.html', form=form)

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.gallery'))


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data, location=form.location.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)