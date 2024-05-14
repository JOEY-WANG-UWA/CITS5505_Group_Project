from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from flask_login import current_user, login_user
import sqlalchemy as sa
from app.models import User
from sqlalchemy.orm import joinedload, aliased
from flask_login import logout_user
from flask import request, g
from urllib.parse import urlsplit
from flask_login import login_required
from app import db
from app.forms import RegistrationForm
from datetime import datetime, timezone
from app.forms import EditProfileForm
from app.forms import PostForm
from app.forms import EmptyForm
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm
from app.forms import SearchForm
from app.forms import MessageForm
from app.models import Message
from app.models import Notification
from flask_babel import _, get_locale
from app.forms import UploadForm
from werkzeug.utils import secure_filename
import os
from app.models import Post, Collection, Favourite, followers
from app.models import Upload, Upload_detail, Comment
from collections import defaultdict
from sqlalchemy import select, func, distinct
from .forms import DescriptionForm
from .forms import CommentForm
from flask import jsonify
import uuid

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()


@ app.route('/')
@ app.route('/gallery')
def gallery():
    uploads = Upload.query.all()
    grouped_details = defaultdict(dict)

    uploads_with_collection = db.session.query(
        Upload.id,
        Upload.title,
        User.username,
        Upload.description,
        Comment.comment_content,
        func.count(distinct(Collection.id)).label('collect_count'),
        func.count(distinct(Comment.id)).label('comment_count')
    ).select_from(Upload).join(User).outerjoin(Collection, Collection.upload_id == Upload.id).outerjoin(Comment, Comment.upload_id == Upload.id).group_by(Upload.id, Upload.title, User.username).all()

    # for upload in uploads_with_collection:
    # print(upload)

    for upload_id, title, username, description, comment, collect_count, comment_count in uploads_with_collection:
        grouped_details[upload_id] = {
            'title': title,
            'username': username,
            'description': description,
            'comment': comment,
            'collect_count': collect_count,
            'comment_count': comment_count,
            'items': []
        }
    for upload in Upload.query.all():
        for detail in upload.updetails:
            grouped_details[upload.id]['items'].append(detail.upload_item)
    print(grouped_details) ##？？？？？？？？？？？
    return render_template('main/gallery.html', grouped_details=grouped_details, uploads=uploads, uploads_with_collection=uploads_with_collection)


if __name__ == '__main__':
    app.run(debug=True)


@app.route('/add_to_collection/<int:upload_id>', methods=['POST'])
def add_to_collection(upload_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    collection = Collection.query.filter_by(
        upload_id=upload_id, user_id=current_user.id).first()
    if collection:
        db.session.delete(collection)
        db.session.commit()
        new_count = Collection.query.filter_by(upload_id=upload_id).count()
        return jsonify({'success': True, 'newCount': new_count})
    else:
        new_collection = Collection(
            upload_id=upload_id, user_id=current_user.id)
        db.session.add(new_collection)
        db.session.commit()
        new_count = Collection.query.filter_by(upload_id=upload_id).count()
        return jsonify({'success': True, 'newCount': new_count})

# @app.route('/add_to_collection/<int:upload_id>', methods=['POST'])
# def add_to_collection(upload_id):
    new_collection = Collection(upload_id=upload_id, user_id=current_user.id)
    db.session.add(new_collection)
    db.session.commit()
    return jsonify({'message': 'Successfully added to collection'})


@app.route('/post_comment/<int:upload_id>', methods=['POST'])
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

    return jsonify({'success': True, 'message': 'Comment posted', 'username': current_user.username})


@app.route('/index', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Home', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data, location=form.location.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

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
        base_query = base_query.filter(Collection.user_id == user_id).join(Collection, Collection.upload_id == Upload.id)
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
        uploads = db.session.query(Upload).join(Collection, Collection.upload_id == Upload.id).filter(Collection.user_id == user_id).all()
    else:
        uploads = db.session.query(Upload).filter_by(user_id=user_id).all()

    for upload in uploads:
        for detail in upload.updetails:
            grouped_details[upload.id]['items'].append(detail.upload_item)

    return list(grouped_details.values())



@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = db.session.query(User).filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('POSTS_PER_PAGE', 10)

    # Fetch data using the helper function
    grouped_details = fetch_data(user.id)

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = grouped_details[start:end]
    total = len(grouped_details)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    comments_with_user = db.session.query(
        Comment.id, Comment.upload_id, Comment.user_id, Comment.comment_content, Comment.comment_time, User.username
    ).join(User, User.id == Comment.user_id).all()


    form = EmptyForm()

    return render_template('user.html', user=user, pagination=pagination, form=form, results=paginated_items,
                           comments_with_user=comments_with_user)


@app.template_filter()
def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

@app.route('/user/<username>/check_collections')
@login_required
def check_collections(username):
    # Fetch the user by username or return 404 if not found
    user = db.session.query(User).filter_by(username=username).first_or_404()

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('POSTS_PER_PAGE', 10)

    # Fetch data for collections using the helper function
    grouped_details = fetch_data(user.id, for_collections=True)

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = grouped_details[start:end]
    total = len(grouped_details)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    comments_with_user = db.session.query(
        Comment.id, Comment.upload_id, Comment.user_id, Comment.comment_content, Comment.comment_time, User.username
    ).join(User, User.id == Comment.user_id).all()
    form = EmptyForm()

    return render_template('User/collections.html', user=user, pagination=pagination, results=paginated_items, form = form,comments_with_user=comments_with_user)


@app.route('/user/<username>/following')
@login_required
def show_following(username):
    user = db.first_or_404(sa.select(User).filter_by(username=username))
    page = request.args.get('page', 1, type=int)
    # We use an aliased User to distinguish between the follower and followed in the join
    followed_alias = aliased(User)

    pagination = db.session.query(followed_alias). \
        join(followers, followers.c.followed_id == followed_alias.id). \
        filter(followers.c.follower_id == user.id). \
        paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    following = pagination.items
    form=EmptyForm()
    return render_template('user/following.html', user=user, form=form, pagination=pagination, following=following)



@app.route('/user/<username>/followers')
@login_required
def show_follower(username):
    user = db.first_or_404(sa.select(User).filter_by(username=username))
    page = request.args.get('page', 1, type=int)
    following_alias = aliased(User)

    pagination = db.session.query(following_alias). \
        join(followers, followers.c.follower_id == following_alias.id). \
        filter(followers.c.followed_id == user.id). \
        paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    follower = pagination.items
    form = EmptyForm()
    return render_template('user/followed.html', user=user, form=form,pagination=pagination, follower=follower)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>', methods=['POST'])
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
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               app.config['POSTS_PER_PAGE'])
    next_url = url_for('search', q=g.search_form.q.data, page=page + 1) \
        if total > page * app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
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
        return redirect(url_for('user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=app.config['POSTS_PER_PAGE'],
                           error_out=False)
    next_url = url_for('messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/notifications')
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


@app.route('/view-details', methods=['GET'])
def view_details():
    # details = sa.select(Upload_detail).order_by(Upload_detail.id.desc())
    details = Upload_detail.query.all()
    uploads = sa.select(Upload).order_by(Upload.id.desc())
    # uploads = Upload.query.all()
    likes = sa.select(Favourite).order_by(Favourite.id.desc())
    # likes = Favourite.query.all()
    # Passing all data sets to the template
    return render_template('view_details.html', details=details, uploads=uploads, likes=likes)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Create a new upload entry
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
                        unique_filename = str(uuid.uuid4()) + "_" + filename
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(file_path)

                        # Create a new upload detail entry
                        new_detail = Upload_detail(
                            upload_id=new_upload.id,
                            upload_item=unique_filename,
                        )
                        db.session.add(new_detail)

                db.session.commit()
                flash('All files successfully uploaded as part of the same post!')
                return redirect(url_for('gallery'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred: ' + str(e), 'error')
                return redirect(url_for('upload'))
        else:
            return jsonify({"errors": form.errors}), 400
    return render_template('upload.html', form=form)
