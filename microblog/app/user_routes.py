from flask import Blueprint, render_template, flash, redirect, url_for,g,request, current_app, jsonify
from flask_login import current_user, login_required
from flask_babel import _
from flask_paginate import Pagination
from werkzeug.utils import secure_filename
from sqlalchemy import  func,  distinct
from sqlalchemy.orm import aliased
from datetime import datetime, timezone
from collections import defaultdict
import os
import uuid
import sqlalchemy as sa
from app import db,Config
from app.forms import (LoginForm, RegistrationForm, EditProfileForm, PostForm,
                       EmptyForm, ResetPasswordRequestForm, ResetPasswordForm,
                       SearchForm, MessageForm, UploadForm,CommentForm)
from app.models import (User, Post, Message, Notification, Upload, Upload_detail,
                        Comment, Collection, Favourite, followers)
from app.email import send_password_reset_email

user_bp = Blueprint('user', __name__)


def fetch_data(user_id, for_collections=False):
    # Query to get the counts of collections and comments for each upload
    counts_query = db.session.query(
        Upload.id.label('upload_id'),
        func.count(distinct(Collection.id)).label('collect_count'),
        func.count(distinct(Comment.id)).label('comment_count')
    ).outerjoin(Collection, Collection.upload_id == Upload.id)\
        .outerjoin(Comment, Comment.upload_id == Upload.id)\
        .group_by(Upload.id).subquery()

    # Base query to get the upload details and filtered by user_id
    base_query = db.session.query(
        Upload.id,
        Upload.title,
        User.username,
        User.avatar,
        Upload.description,
        counts_query.c.collect_count,
        counts_query.c.comment_count
    ).select_from(Upload).join(User)\
        .outerjoin(counts_query, counts_query.c.upload_id == Upload.id)

    if for_collections:
        base_query = base_query.filter(Collection.user_id == user_id).join(
            Collection, Collection.upload_id == Upload.id)
    else:
        base_query = base_query.filter(Upload.user_id == user_id)

    uploads_with_collection = base_query.all()

    grouped_details = defaultdict(dict)
    for upload_id, title, username, avatar, description, collect_count, comment_count in uploads_with_collection:
        grouped_details[upload_id] = {
            'upload_id': upload_id,
            'title': title,
            'username': username,
            'avatar': avatar,
            'description': description,
            'collect_count': collect_count,
            'comment_count': comment_count,
            'items': []
        }

    if for_collections:
        uploads = db.session.query(Upload).join(
            Collection, Collection.upload_id == Upload.id).filter(Collection.user_id == user_id).all()
    else:
        uploads = db.session.query(Upload).filter_by(user_id=user_id).all()

    for upload in uploads:
        for detail in upload.updetails:
            grouped_details[upload.id]['items'].append(detail.upload_item)
    print(grouped_details)
    return list(grouped_details.values())


@user_bp.route('/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = db.session.query(User).filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    per_page = Config.POSTS_PER_PAGE

    # Fetch data using the helper function
    grouped_details = fetch_data(user.id)

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = grouped_details[start:end]
    total = len(grouped_details)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # comments_with_user = db.session.query(
    #    Comment.id, Comment.upload_id, Comment.user_id, Comment.comment_content, Comment.comment_time, User.username
    # ).join(User, User.id == Comment.user_id).all()

    comments_with_user = db.session.query(
        Upload.id,
        Comment.comment_content,
        Comment.comment_time,
        User.username
    ).select_from(Comment).join(User).outerjoin(Upload, Upload.id == Comment.upload_id).all()

    form = EmptyForm()

    return render_template('user.html', user=user, pagination=pagination, form=form, results=paginated_items,
                           comments_with_user=comments_with_user)



def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@user_bp.route('/<username>/check_collections')
@login_required
def check_collections(username):
    # Fetch the user by username or return 404 if not found
    user = db.session.query(User).filter_by(username=username).first_or_404()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    per_page = Config.POSTS_PER_PAGE

    # Fetch data for collections using the helper function
    grouped_details = fetch_data(user.id, for_collections=True)

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = grouped_details[start:end]
    total = len(grouped_details)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # comments_with_user = db.session.query(
    #    Comment.id, Comment.upload_id, Comment.user_id, Comment.comment_content, Comment.comment_time, User.username
    # ).join(User, User.id == Comment.user_id).all()
    form = EmptyForm()

    comments_with_user = db.session.query(
        Upload.id,
        Comment.comment_content,
        Comment.comment_time,
        User.username
    ).select_from(Comment).join(User).outerjoin(Upload, Upload.id == Comment.upload_id).all()

    print(comments_with_user)
    return render_template('User/collections.html', user=user, pagination=pagination, results=paginated_items, form=form, comments_with_user=comments_with_user)


@user_bp.route('/<username>/following')
@login_required
def show_following(username):
    user = db.first_or_404(sa.select(User).filter_by(username=username))
    page = request.args.get('page', 1, type=int)
    # We use an aliased User to distinguish between the follower and followed in the join
    followed_alias = aliased(User)

    pagination = db.session.query(followed_alias). \
        join(followers, followers.c.followed_id == followed_alias.id). \
        filter(followers.c.follower_id == user.id). \
        paginate(
            page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)

    following = pagination.items
    form = EmptyForm()
    return render_template('User/following.html', user=user, form=form, pagination=pagination, following=following)


@user_bp.route('/<username>/followers')
@login_required
def show_follower(username):
    user = db.first_or_404(sa.select(User).filter_by(username=username))
    page = request.args.get('page', 1, type=int)
    following_alias = aliased(User)

    pagination = db.session.query(following_alias). \
        join(followers, followers.c.follower_id == following_alias.id). \
        filter(followers.c.followed_id == user.id). \
        paginate(
            page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)

    follower = pagination.items
    form = EmptyForm()
    return render_template('User/followed.html', user=user, form=form, pagination=pagination, follower=follower)


@user_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data

        if form.avatar.data:
            avatar_file = form.avatar.data
            filename = secure_filename(avatar_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            avatar_path = os.path.join(
                (Config.AVATAR_UPLOAD_FOLDER), unique_filename)
            avatar_file.save(avatar_path)
            current_user.avatar = unique_filename
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user.user', username=username))
    else:
        return redirect(url_for('main.index'))


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user.user', username=username))
    else:
        return redirect(url_for('main.index'))


@user_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('main.login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', form=form)




@user_bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count',
                              user.unread_message_count())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('user.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@user_bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=Config.POSTS_PER_PAGE,
                           error_out=False)
    next_url = url_for('user.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('user.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@user_bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]


@user_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            new_upload = Upload(
                user_id=current_user.id,
                title=form.title.data,
                hashtag=form.hashtag.data,
                description=form.description.data,
                upload_time=datetime.now(timezone.utc)
            )
            db.session.add(new_upload)
            db.session.flush()

            # Process each file in the request
            files = request.files.getlist('file')
            for file in files:
                if file:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{new_upload.id}_{filename}"
                    file_path = os.path.join(
                        (Config.UPLOAD_FOLDER), unique_filename)
                    file.save(file_path)

                    new_detail = Upload_detail(
                        upload_id=new_upload.id,
                        upload_item=unique_filename,
                    )
                    db.session.add(new_detail)

            db.session.commit()
            flash('All files successfully uploaded as part of the same post!')
            return redirect(url_for('main.gallery'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error occurred: {str(e)}')
            flash('An error occurred: ' + str(e), 'error')
            return redirect(url_for('user.upload'))
    return render_template('upload.html', form=form)
