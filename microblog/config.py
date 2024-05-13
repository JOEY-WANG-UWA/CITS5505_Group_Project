import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    POSTS_PER_PAGE = 3
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    ADMINS = ['joey.wang.uwa@gmail.com']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  ###
    UPLOAD_PATH = os.path.join(basedir, 'uploads') # Path to the folder where uploaded files will be stored
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_MAX_FILE_SIZE = 3
    DROPZONE_PARALLEL_UPLOADS = 9
    UPLOAD_FOLDER = '/Users/imac/Desktop/z/CITS5505_Group_Project1/microblog/Upload'####