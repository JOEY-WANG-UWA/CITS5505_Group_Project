from flask import Blueprint, render_template,  redirect, url_for,g,request
from flask_login import login_required
from flask_babel import _
from app import db
from app.models import (User, Post, Message, Notification, Upload, Upload_detail,
                        Comment, Collection, Favourite, followers)

search_bp = Blueprint('search_bp', __name__)
# Add your routes here

@search_bp.route('/search_route')
def search_route():
    return "Search route"

def add_to_index(index, model):
    if not app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    app.elasticsearch.index(index=index, id=model.id, document=payload)

def remove_from_index(index, model):
    if not app.elasticsearch:
        return
    app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, page, per_page):
    if not app.elasticsearch:
        return [], 0
    search = app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']

@search_bp.route('/search')
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
