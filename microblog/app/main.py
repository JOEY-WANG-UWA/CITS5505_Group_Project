from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from flask_login import current_user, login_user
import sqlalchemy as sa
from app.models import User
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
from app.models import Post
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm
from app.forms import SearchForm
from app.forms import MessageForm
from app.models import Message
from app.models import Notification
from app.models import Upload
from app.models import Upload_detail
from app.models import Favourite
from flask_babel import _, get_locale
from sqlalchemy import select, func
from app.models import User, Comment, Collection
from collections import defaultdict


@app.route('/', methods=['GET', 'POST'])
# def gallery():
# details = Upload_detail.query.all()
# return render_template("main/gallery.html", details=details)
@app.route('/')
def gallery():
    uploads = Upload.query.all()
    grouped_details = defaultdict(list)
    for upload in uploads:
        for detail in upload.updetails:
            grouped_details[upload.id].append(detail)

    return render_template('main/gallery.html', grouped_details=grouped_details)

    details = db.session.scalars(
        select(Upload_detail).order_by(func.random()).limit(16)
    ).all()
    return render_template('main/photo.html', details=details)


@app.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = db.get_or_404(Photo, photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_COMMENT_PER_PAGE']
    pagination = db.paginate(
        select(Comment).filter_by(photo_id=photo.id).order_by(
            Comment.created_at.asc()),
        page=page,
        per_page=per_page
    )
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    description_form.description.data = photo.description
    return render_template('main/photo.html', photo=photo, comment_form=comment_form,
                           description_form=description_form, tag_form=tag_form,
                           pagination=pagination, comments=comments)
