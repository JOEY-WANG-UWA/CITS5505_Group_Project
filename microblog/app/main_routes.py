from flask import Blueprint, render_template, flash, redirect, url_for, g, request, current_app, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from sqlalchemy import select, func, or_, distinct
from datetime import datetime, timezone
from collections import defaultdict
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, EmptyForm, ResetPasswordRequestForm, ResetPasswordForm, SearchForm, MessageForm, UploadForm, CommentForm
from app.models import User, Post, Message, Notification, Upload, Upload_detail, Comment, Collection, Favourite, followers
from app import db, Config

main_bp = Blueprint('main', __name__)


@main_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()


def fetch_data_gallery():
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
            'items': []  # Initialize items as an empty list
        }

    uploads = Upload.query.all()
    for upload in uploads:
        for detail in upload.updetails:
            grouped_details[upload.id]['items'].append(detail.upload_item)

    return grouped_details


@main_bp.route('/')
@main_bp.route('/gallery')
def gallery():
    grouped_details = fetch_data_gallery()
    comments_with_user = db.session.query(
        Upload.id,
        Comment.comment_content,
        Comment.comment_time,
        User.username
    ).select_from(Comment).join(User).outerjoin(Upload, Upload.id == Comment.upload_id).all()

    return render_template('main/gallery_view.html', grouped_details=grouped_details, comments_with_user=comments_with_user)


@main_bp.route('/add_to_collection/<int:upload_id>', methods=['POST'])
@login_required
def add_to_collection(upload_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    collection = Collection.query.filter_by(
        upload_id=upload_id, user_id=current_user.id).first()
    if collection:
        db.session.delete(collection)
        db.session.commit()
        new_count = Collection.query.filter_by(upload_id=upload_id).count()
        return jsonify({'success': True, 'newCount': new_count, 'liked': False})
    else:
        new_collection = Collection(
            upload_id=upload_id, user_id=current_user.id)
        db.session.add(new_collection)
        db.session.commit()
        new_count = Collection.query.filter_by(upload_id=upload_id).count()
        return jsonify({'success': True, 'newCount': new_count, 'liked': True})


@main_bp.route('/post_comment/<int:upload_id>', methods=['POST'])
def post_comment(upload_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    data = request.get_json()
    comment_content = data.get('comment')

    if not comment_content:
        return jsonify({'success': False, 'message': 'Comment content is required'}), 400

    new_comment = Comment(
        upload_id=upload_id,
        user_id=current_user.id,
        comment_content=comment_content
    )
    db.session.add(new_comment)
    db.session.commit()
    new_count = Comment.query.filter_by(upload_id=upload_id).count()
    return jsonify({'success': True, 'newCount': new_count, 'message': 'Comment posted', 'username': current_user.username, 'comment_time': new_comment.comment_time.strftime('%Y-%m-%d %H:%M:%S')})


@main_bp.route('/index', methods=['GET', 'POST'])
@login_required
def circus():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=Config.POSTS_PER_PAGE, error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Circus', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


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
        return redirect(url_for('main.gallery'))
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
